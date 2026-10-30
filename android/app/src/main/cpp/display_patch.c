// Frame rate and resolution for the 3.7.1 game, chosen in Pod Programs.
//
// Runs in the game's process before Unity starts (see DisplayPatch.java). It
// loads the game library first and rewrites a few instructions in memory:
//
// - Frame rate: the game sets Application.targetFrameRate to 30 at start (two
//   places), and its performance presets ask OnDemandRendering for 30 frames
//   (Dark.Component.PerformanceSetting.Config, UnSavePowerTargetRenderFrameRate).
//   Both become the chosen rate (up to the screen's maximum refresh rate).
//   Power saving keeps its own 10 frames.
// - Resolution: the presets with effects on (the start preset, Highest and
//   High) and the first resolution the game sets use the chosen RenderTargetSize.
//   RenderManager never goes above the screen's own resolution.
// - Battles: BattleUpdate advances the battle by one 30 Hz step per frame. It
//   now advances it by one whole step each time 1/30 s of frame time has
//   built up, and skips the frames in between. Fractional steps crashed the
//   summon reveal, which runs on the battle code.
// - Field movement: ActorController moves characters in FixedUpdate by its
//   time step, but runs once per rendered frame while physics keeps the 1/30 s
//   step, so at 60 frames characters move twice as fast. Once per frame the
//   physics step is set to that frame's duration (1/240 to 1/30 s); measured
//   on a Galaxy Fold at 60, walking then matches 30 fps (3.7 m/s).
// - Story-event zones: a zone the player walks through while an event's
//   balloon fades out still counts (see the notes above state_changing). This
//   one applies at every frame rate, the game's own 30 included.
// - Special Gift Roulette: IronSource.showRewardedVideo raises the video's
//   "rewarded" and "closed" events at once instead (roulette_ads.c). This one
//   applies with any settings too.
// - Text builder: ArtStringBuilder grows its buffer to fit long text instead of
//   writing past its end (text_buffer.c). This one applies with any settings too.
// - Snapping lists (the summon banners): DarkScrollRect.UpdateSnapPosition eases
//   the list to the chosen row with SmoothDamp and counts it as there within
//   0.01. Above 30 fps each frame's step is so small that, far down a long list,
//   it is below the position's float precision: the list stops just short,
//   keeps a small speed, and IsScrolling stays true, so the Summon buttons
//   ignore taps. It now counts as there within 1 unit (invisible). Any setting.
//
// 【rev D·L3b】RVA tables are now per-client (EN / JP). Every site is checked
// before any write, and every write is verified by reading the patched bytes
// back.
// 【rev D·L4】The client is now detected by region consistency: the declared
// region (manifest meta-data org.veritr1x.bunker.REGION) and the package name
// are cross-checked against the loaded libil2cpp.so file size, all three
// through the same JP/EN fact table as lunar-scripts-zh/shared/detect_client.py
// (REGIONS). Any contradiction or unknown value rejects the patch (fail-fast,
// never mixes tables, no default branch).
#include <android/log.h>
#include <dlfcn.h>
#include <jni.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <sys/mman.h>
#include <unistd.h>

#include "roulette_ads.h"
#include "text_buffer.h"

enum { FullHD = 6, WQHD = 7, DeviceMax = 8 };

typedef struct { uint32_t rva, original, patched; } Site;

// ---------------------------------------------------------------------------
// 【rev D·L3b】Per-client RVA table
// ---------------------------------------------------------------------------
// All patch-site and hook RVAs for each supported client.  The original words
// (signature checks) are identical across clients; only the addresses differ.
typedef struct {
    // sites() – frame rate and resolution word patches
    uint32_t fps_onlywhenstarting;
    uint32_t fps_setuprenderer;
    uint32_t fps_config_ccor;
    uint32_t res_config_start_high;
    uint32_t res_config_highest;
    uint32_t res_rendermgr_delaystart;
    // kSnapArrive – snapping-lists tolerance patch
    uint32_t snap_arrive;
    // hook sites – 4-instruction trampolines
    uint32_t hook_fixedprocess;
    uint32_t hook_battlestep;
    uint32_t hook_changestate;
    uint32_t hook_triggerenter;
    // roulette (warning-only, may be 0 when unresolved)
    uint32_t hook_showrewardedvideo;
    // support functions called by hook code
    uint32_t time_unscaled_delta;
    uint32_t time_fixed_delta;
    uint32_t time_set_fixed_delta;
    uint32_t time_frame_count;
    uint32_t battle_process;
    uint32_t stay_on_stay;
    uint32_t stay_begin;
    uint32_t empty_onstateupdate;
} ClientRvas;

// EN 3.7.1 (com.square_enix.android_googleplay.nierspww, libil2cpp.so 127 359 872 B)
static const ClientRvas kEnRvas = {
    .fps_onlywhenstarting    = 0x2E5BE0C,
    .fps_setuprenderer       = 0x2E5C31C,
    .fps_config_ccor         = 0x2C7AC80,
    .res_config_start_high   = 0x2C7ACD8,
    .res_config_highest      = 0x2C7AD10,
    .res_rendermgr_delaystart= 0x2EC1D04,
    .snap_arrive             = 0x30DF5A0,
    .hook_fixedprocess       = 0x2D5F7A0,
    .hook_battlestep         = 0x2A6530C,
    .hook_changestate        = 0x3A0ECF8,
    .hook_triggerenter       = 0x363082C,
    .hook_showrewardedvideo  = 0x3291FB4,
    .time_unscaled_delta     = 0x4D7ED90,
    .time_fixed_delta        = 0x4D7EDC4,
    .time_set_fixed_delta    = 0x4D7EDF8,
    .time_frame_count        = 0x4D7EF50,
    .battle_process          = 0x37DC3D0,
    .stay_on_stay            = 0x2984420,
    .stay_begin              = 0x2984210,
    .empty_onstateupdate     = 0x3A05C64,
};

// JP 3.7.1 (com.square_enix.android_googleplay.nierspjp, libil2cpp.so 126 216 336 B)
static const ClientRvas kJpRvas = {
    .fps_onlywhenstarting    = 0x2E5E8FC,
    .fps_setuprenderer       = 0x2E5EE0C,
    .fps_config_ccor         = 0x2C6E934,
    .res_config_start_high   = 0x2C6E98C,
    .res_config_highest      = 0x2C6E9C4,
    .res_rendermgr_delaystart= 0x31C09A0,
    .snap_arrive             = 0x2CCAFD0,
    .hook_fixedprocess       = 0x2D06248,
    .hook_battlestep         = 0x29AFF7C,
    .hook_changestate        = 0x39AD0D8,
    .hook_triggerenter       = 0x35659E4,
    // JP showRewardedVideo: 4 candidates, unresolved → 0 → warning-only skip
    .hook_showrewardedvideo  = 0,
    .time_unscaled_delta     = 0x4CA9C30,
    .time_fixed_delta        = 0x4CA9C98,
    .time_set_fixed_delta    = 0x4CA9D00,
    .time_frame_count        = 0x4CA9F70,
    .battle_process          = 0x3762E14,
    .stay_on_stay            = 0x29BBA48,
    .stay_begin              = 0x29BB838,
    .empty_onstateupdate     = 0x39A4044,
};

// 【rev D·L4】Region fact table, aligned with lunar-scripts-zh/shared/
// detect_client.py REGIONS and android/tools/region.py REGIONS (same region
// keys, game package names and libil2cpp.so sizes — one JP/EN fact table).
// Drift between the three copies is refused by l3b-test/test_display_rva.py
// and android/tools/test_display.py.
#define EN_LIB_SIZE 127359872LL   // com.square_enix.android_googleplay.nierspww (en)
#define JP_LIB_SIZE 126216336LL   // com.square_enix.android_googleplay.nierspjp (jp)

typedef struct {
    const char *region;    // "en" / "jp" — region.py / detect_client.py key
    const char *package;   // the client APK's manifest package
    long long lib_size;    // libil2cpp.so file size (runtime evidence)
    const ClientRvas *rvas;
} ClientFact;

static const ClientFact kClients[] = {
    {"en", "com.square_enix.android_googleplay.nierspww", EN_LIB_SIZE, &kEnRvas},
    {"jp", "com.square_enix.android_googleplay.nierspjp", JP_LIB_SIZE, &kJpRvas},
};

static const ClientFact *fact_for_region(const char *region) {
    if (!region || !*region) return NULL;
    for (size_t i = 0; i < sizeof kClients / sizeof kClients[0]; i++)
        if (!strcmp(kClients[i].region, region)) return &kClients[i];
    return NULL;
}

static const ClientFact *fact_for_package(const char *package) {
    if (!package || !*package) return NULL;
    for (size_t i = 0; i < sizeof kClients / sizeof kClients[0]; i++)
        if (!strcmp(kClients[i].package, package)) return &kClients[i];
    return NULL;
}

static const ClientFact *fact_for_size(long long size) {
    for (size_t i = 0; i < sizeof kClients / sizeof kClients[0]; i++)
        if (kClients[i].lib_size == size) return &kClients[i];
    return NULL;
}

/**
 * 【rev D·L4】Region-consistency detection: which client's table this binary
 * may be patched with. Three declaration sources are cross-checked against
 * the loaded libil2cpp.so's file size:
 *
 *   declared_region  — manifest meta-data org.veritr1x.bunker.REGION
 *                      (written at packaging: package_game.py / assemble_apk.py),
 *                      or "" when the build predates it;
 *   declared_package — the process package name (the client APK's package
 *                      from region.py's triple), or "" when unavailable;
 *   lib size         — stat() of the library actually loaded.
 *
 * Every present source must map to a known client and agree with the size.
 * A contradiction or an unknown value fails fast (NULL): the patch is never
 * applied with a table that has not been proven to belong to this binary.
 * An absent declaration is simply absent (size alone decides, as before);
 * 口径同 detect_client.py: 未知/矛盾一律拒，无默认分支、不猜测.
 */
static const ClientFact *detect_client(const char *lib_path,
                                       const char *declared_region,
                                       const char *declared_package) {
    struct stat st;
    if (!lib_path || stat(lib_path, &st) != 0) return NULL;
    const ClientFact *by_size = fact_for_size(st.st_size);
    if (!by_size) {
        __android_log_print(ANDROID_LOG_WARN, "Bunker",
                            "Display patch: libil2cpp.so size %lld is not a known client; refusing to patch",
                            (long long)st.st_size);
        return NULL;
    }
    const ClientFact *by_region = fact_for_region(declared_region);
    if (declared_region && *declared_region && !by_region) {
        __android_log_print(ANDROID_LOG_WARN, "Bunker",
                            "Display patch: declared region '%s' is not a known client; refusing to patch",
                            declared_region);
        return NULL;
    }
    const ClientFact *by_package = fact_for_package(declared_package);
    if (declared_package && *declared_package && !by_package) {
        __android_log_print(ANDROID_LOG_WARN, "Bunker",
                            "Display patch: package '%s' is not a known client; refusing to patch",
                            declared_package);
        return NULL;
    }
    if (by_region && by_region != by_size) {
        __android_log_print(ANDROID_LOG_WARN, "Bunker",
                            "Display patch: declared region '%s' contradicts libil2cpp.so (%s table); refusing to patch",
                            declared_region, by_size->region);
        return NULL;
    }
    if (by_package && by_package != by_size) {
        __android_log_print(ANDROID_LOG_WARN, "Bunker",
                            "Display patch: package '%s' contradicts libil2cpp.so (%s table); refusing to patch",
                            declared_package, by_size->region);
        return NULL;
    }
    return by_size;
}

// ---------------------------------------------------------------------------
// End of per-client RVA table
// ---------------------------------------------------------------------------

static uint32_t mov_w(int reg, int value) { return 0x52800000u | (uint32_t)value << 5 | (uint32_t)reg; }

// orr x11, x11, #(size << 32): the immediate is encoded as a run of set bits.
static uint32_t orr_x11_size(int size) {
    switch (size) {
    case FullHD: return 0xb25f056bu;
    case WQHD: return 0xb260096bu;
    default: return 0xb25d016bu;
    }
}

static int sites(const ClientRvas *rvas, int fps, int size, Site *out) {
    int n = 0;
    if (fps) {
        out[n++] = (Site){rvas->fps_onlywhenstarting, 0x321f0fe0u, mov_w(0, fps)};  // Generator.OnlyWhenStarting: targetFrameRate = 30
        out[n++] = (Site){rvas->fps_setuprenderer, 0x321f0fe0u, mov_w(0, fps)};    // Generator.SetupRenderer: targetFrameRate = 30
        out[n++] = (Site){rvas->fps_config_ccor, 0x321f0fe9u, mov_w(9, fps)};      // Config..cctor: UnSavePowerTargetRenderFrameRate = 30
    }
    if (size) {
        out[n++] = (Site){rvas->res_config_start_high, 0xd2c000aau, 0xd2c0000au | (uint32_t)size << 5};  // Config..cctor: HD for the start preset and High
        out[n++] = (Site){rvas->res_config_highest, 0xb25f056bu, orr_x11_size(size)};                    // Config..cctor: FullHD for Highest
        out[n++] = (Site){rvas->res_rendermgr_delaystart, 0x528000a1u, mov_w(1, size)};                  // RenderManager.DelayStart: HD at start
    }
    return n;
}

static int write_word(uint32_t *address, uint32_t value) {
    uintptr_t page = (uintptr_t)sysconf(_SC_PAGESIZE);
    void *start = (void *)((uintptr_t)address & ~(page - 1));
    if (mprotect(start, page, PROT_READ | PROT_WRITE | PROT_EXEC)) return -1;
    *(volatile uint32_t *)address = value;
    __builtin___clear_cache((char *)address, (char *)(address + 1));
    mprotect(start, page, PROT_READ | PROT_EXEC);
    return 0;
}

// 【rev D·L3b】Write a word and assert the patched bytes read back correctly.
static int write_word_assert(uint32_t *address, uint32_t value) {
    if (write_word(address, value)) return -1;
    if (*address != value) return -2;  // byte assertion failed
    return 0;
}

// UpdateSnapPosition: "ldr s0, [x8, #0x18]" (kScrollBorder, 0.01) becomes "fmov s0, #1.0".
static const Site kSnapArriveOriginal = {0, 0xBD401900u, 0x1E2E1000u};  // RVA filled from ClientRvas

// Unity's Time accessors, from the same metadata.
static float (*time_unscaled_delta)(void *method);
static float (*time_fixed_delta)(void *method);
static void (*time_set_fixed_delta)(float value, void *method);
static int (*time_frame_count)(void *method);
static int last_frame = -1;

/** Runs at the start of ActorController.FixedProcess, on Unity's main thread. */
__attribute__((visibility("hidden"), used)) void follow_frame_time(void) {
    int frame = time_frame_count(NULL);
    if (frame == last_frame) return;
    last_frame = frame;
    float step = time_unscaled_delta(NULL);
    if (step < 1 / 240.f) step = 1 / 240.f;
    if (step > 1 / 30.f) step = 1 / 30.f;
    if (time_fixed_delta(NULL) != step) time_set_fixed_delta(step, NULL);
}

static double battle_time;

/** Whether BattleUpdate.OnStateUpdate runs a 30 Hz step this frame: 1 once 1/30 s has built up, else 0. */
__attribute__((visibility("hidden"), used)) int battle_step(void) {
    battle_time += 30.0 * time_unscaled_delta(NULL);
    if (battle_time < 1.0) return 0;
    // At most one step per frame, as before; a long frame doesn't build a backlog.
    battle_time = battle_time >= 2.0 ? 0.0 : battle_time - 1.0;
    return 1;
}

// Replaces four instructions with "ldr x16, #8; br x16; <hook address>". The
// first word is the "already hooked" marker.
static int hook(uint32_t *at, const uint32_t original[4], void (*target)(void)) {
    if (at[0] == 0x58000050u) return 0;
    for (int i = 0; i < 4; i++) if (at[i] != original[i]) return -1;
    uintptr_t page = (uintptr_t)sysconf(_SC_PAGESIZE), start = (uintptr_t)at & ~(page - 1);
    if (mprotect((void *)start, page * 2, PROT_READ | PROT_WRITE | PROT_EXEC)) return -1;
    at[0] = 0x58000050u;  // ldr x16, #8
    at[1] = 0xd61f0200u;  // br x16
    *(volatile uint64_t *)&at[2] = (uint64_t)(uintptr_t)target;
    __builtin___clear_cache((char *)at, (char *)(at + 4));
    mprotect((void *)start, page * 2, PROT_READ | PROT_EXEC);
    return 0;
}

// BattleUpdate.OnStateUpdate ends with "fmov d0, #1.0; mov w1, wzr; mov x2, xzr;
// ldp x20, x19, [sp], #0x20; b KernelBattle.Process": the hook makes that call only
// when battle_step() is 1, and otherwise returns.
static const uint32_t kBattleStepCall[4] = {0x1e6e1000u, 0x2a1f03e1u, 0xaa1f03e2u, 0xa8c24ff4u};
__attribute__((visibility("hidden"), used)) uintptr_t battle_process;
__attribute__((naked)) static void battle_step_hook(void) {
    __asm__ volatile(
        "stp x0, x30, [sp, #-16]!\n"
        "bl battle_step\n"
        "mov w17, w0\n"
        "ldp x0, x30, [sp], #16\n"
        "ldp x20, x19, [sp], #0x20\n"
        "cbz w17, 1f\n"
        "fmov d0, #1.0\n"
        "mov w1, wzr\n"
        "mov x2, xzr\n"
        "adrp x16, battle_process\n"
        "ldr x16, [x16, :lo12:battle_process]\n"
        "br x16\n"
        "1: ret\n");
}

// FixedProcess(this, float deltaTime, MethodInfo*) starts with these four instructions;
// the hook runs them after follow_frame_time and continues at the fifth.
static const uint32_t kFixedProcessPrologue[4] = {0xd10283ffu, 0x6d033befu, 0x6d0433edu, 0x6d052bebu};
__attribute__((visibility("hidden"), used)) uintptr_t fixed_process_resume;
__attribute__((naked)) static void fixed_process_hook(void) {
    __asm__ volatile(
        "stp x0, x1, [sp, #-32]!\n"
        "stp x30, xzr, [sp, #16]\n"
        "str s0, [sp, #24]\n"
        "bl follow_frame_time\n"
        "ldr s0, [sp, #24]\n"
        "ldr x30, [sp, #16]\n"
        "ldp x0, x1, [sp], #32\n"
        "sub sp, sp, #0xa0\n"
        "stp d15, d14, [sp, #0x30]\n"
        "stp d13, d12, [sp, #0x40]\n"
        "stp d11, d10, [sp, #0x50]\n"
        "adrp x16, fixed_process_resume\n"
        "ldr x16, [x16, :lo12:fixed_process_resume]\n"
        "br x16\n");
}

// Story-event zones. An event state waits for the player to walk into a zone
// (EventTriggerOnEnterCollision) for a few seconds; when that times out, the
// event plays a 1.5 s balloon fade and then waits on the same zone with
// EventTriggerOnEnterCollision plus EventTriggerOnStayCollision. A player who
// walks into the zone during the fade has left it before that fallback starts,
// so neither fires and the event never continues (6-4: Levania walks off the
// map). Even at 30 fps a steady walk reaches 6-4's second zone 2 ms before
// its time-out; above 30 the faster story text and frame timing put players in
// that gap. When such a fallback starts, a collider that entered its zone in
// the last 10 s is passed to EventTriggerOnStayCollision.OnStay, which checks
// it is the player's and continues the event as if they were still there.
typedef struct { void *zone, *collider; double time; } ZoneEntry;
static ZoneEntry zone_entries[32];
static int zone_next;
typedef struct { void *conductor; double since; } ZoneFallback;
static ZoneFallback zone_fallbacks[8];
static void *stay_class, *enter_class;
static void (*stay_on_stay)(void *self, void *collider, void *method);
static uintptr_t stay_begin, stay_update_original;

static double now_seconds(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}

/** Runs at the start of ColliderBase.OnTriggerEnter: remembers who entered which zone. */
__attribute__((visibility("hidden"), used)) void zone_entered(void *zone, void *collider) {
    zone_entries[zone_next] = (ZoneEntry){zone, collider, now_seconds()};
    zone_next = (zone_next + 1) % 32;
}

/** EventTriggerOnStayCollision's OnStateUpdate (an empty virtual it inherits). */
static void stay_update(void *self, void *method) {
    for (int i = 0; i < 8; i++) {
        if (zone_fallbacks[i].conductor != self) continue;
        double since = zone_fallbacks[i].since;
        zone_fallbacks[i].conductor = NULL;
        void *zone = *(void **)((char *)self + 0x50);
        for (int e = 0; zone && e < 32 && !*((uint8_t *)self + 0x59); e++)
            // A destroyed collider (its scene unloading) has a null m_CachedPtr.
            if (zone_entries[e].zone == zone && zone_entries[e].time >= since - 10
                && *(void **)((char *)zone_entries[e].collider + 0x10)) {
                stay_on_stay(self, zone_entries[e].collider, NULL);
                if (*((uint8_t *)self + 0x59))
                    __android_log_print(ANDROID_LOG_INFO, "Bunker", "Story event continued: the player passed its zone %.1f s ago",
                                        since - zone_entries[e].time);
            }
    }
    if (stay_update_original) ((void (*)(void *, void *))stay_update_original)(self, method);
}

/** Points the class's OnStateUpdate slot (after OnStateBegin) at stay_update. */
// 【rev D·L3b】empty_onstateupdate RVA comes from ClientRvas.
static void route_stay_update(void *klass, uint8_t *base, uint32_t empty_rva) {
    uintptr_t *slots = klass;
    for (int i = 0; i < 0x100; i++) {
        if (slots[i] != stay_begin) continue;
        if (slots[i + 2] == (uintptr_t)(base + empty_rva)) {
            stay_update_original = slots[i + 2];
            slots[i + 2] = (uintptr_t)stay_update;
        }
        return;
    }
}

static uint8_t *game_base;

// Global pointer to the active client's RVA table (set in apply()).
static const ClientRvas *g_current_rvas;

/** Runs at the start of InternalFiniteStateMachine.ChangeState with the next state. */
__attribute__((visibility("hidden"), used)) void state_changing(void *state) {
    void *list = state ? *(void **)((char *)state + 0x48) : NULL;
    void *items = list ? *(void **)((char *)list + 0x10) : NULL;
    int size = list ? *(int *)((char *)list + 0x18) : 0;
    void *stay = NULL, *stay_zone = NULL, *enter_zone = NULL;
    for (int i = 0; items && i < size && i < 8; i++) {
        void *conductor = ((void **)((char *)items + 0x20))[i];
        void *klass = conductor ? *(void **)conductor : NULL;
        if (!klass) continue;
        if (!stay_class && !strcmp(*(const char **)((char *)klass + 0x10), "EventTriggerOnStayCollision")) {
            stay_class = klass;
            // 【rev D·L3b】Use per-client empty_onstateupdate RVA.
            route_stay_update(klass, game_base, g_current_rvas ? g_current_rvas->empty_onstateupdate : 0x3A05C64);
        }
        if (!enter_class && !strcmp(*(const char **)((char *)klass + 0x10), "EventTriggerOnEnterCollision")) enter_class = klass;
        if (klass == stay_class) { stay = conductor; stay_zone = *(void **)((char *)conductor + 0x50); }
        if (klass == enter_class) enter_zone = *(void **)((char *)conductor + 0x58);
    }
    if (!stay || !stay_zone || stay_zone != enter_zone) return;
    int slot = 0;
    for (int i = 0; i < 8; i++) if (zone_fallbacks[i].conductor == stay || !zone_fallbacks[i].conductor) { slot = i; break; }
    zone_fallbacks[slot] = (ZoneFallback){stay, now_seconds()};
}

static const uint32_t kChangeState[4] = {0xa9ba6ffcu, 0xa90167fau, 0xa9025ff8u, 0xa90357f6u};
__attribute__((visibility("hidden"), used)) uintptr_t change_state_resume;
__attribute__((naked)) static void change_state_hook(void) {
    __asm__ volatile(
        "stp x0, x1, [sp, #-48]!\n"
        "stp x2, x3, [sp, #16]\n"
        "str x30, [sp, #32]\n"
        "mov x0, x1\n"
        "bl state_changing\n"
        "ldr x30, [sp, #32]\n"
        "ldp x2, x3, [sp, #16]\n"
        "ldp x0, x1, [sp], #48\n"
        "stp x28, x27, [sp, #-0x60]!\n"
        "stp x26, x25, [sp, #0x10]\n"
        "stp x24, x23, [sp, #0x20]\n"
        "stp x22, x21, [sp, #0x30]\n"
        "adrp x16, change_state_resume\n"
        "ldr x16, [x16, :lo12:change_state_resume]\n"
        "br x16\n");
}

static const uint32_t kTriggerEnter[4] = {0xf81d0ff5u, 0xa9014ff4u, 0xa9027bfdu, 0x910083fdu};
__attribute__((visibility("hidden"), used)) uintptr_t trigger_enter_resume;
__attribute__((naked)) static void trigger_enter_hook(void) {
    __asm__ volatile(
        "stp x0, x1, [sp, #-48]!\n"
        "stp x2, x3, [sp, #16]\n"
        "str x30, [sp, #32]\n"
        "bl zone_entered\n"
        "ldr x30, [sp, #32]\n"
        "ldp x2, x3, [sp, #16]\n"
        "ldp x0, x1, [sp], #48\n"
        "str x21, [sp, #-0x30]!\n"
        "stp x20, x19, [sp, #0x10]\n"
        "stp x29, x30, [sp, #0x20]\n"
        "add x29, sp, #0x20\n"
        "adrp x16, trigger_enter_resume\n"
        "ldr x16, [x16, :lo12:trigger_enter_resume]\n"
        "br x16\n");
}

static int hook_event_zones(uint8_t *base, const ClientRvas *rvas) {
    game_base = base;
    g_current_rvas = rvas;
    stay_on_stay = (void (*)(void *, void *, void *))(base + rvas->stay_on_stay);
    stay_begin = (uintptr_t)(base + rvas->stay_begin);
    change_state_resume = (uintptr_t)(base + rvas->hook_changestate + 16);
    trigger_enter_resume = (uintptr_t)(base + rvas->hook_triggerenter + 16);
    if (hook((uint32_t *)(base + rvas->hook_changestate), kChangeState, change_state_hook)) return -1;
    return hook((uint32_t *)(base + rvas->hook_triggerenter), kTriggerEnter, trigger_enter_hook);
}

static int hook_frame_rate(uint8_t *base, const ClientRvas *rvas) {
    time_unscaled_delta = (float (*)(void *))(base + rvas->time_unscaled_delta);
    time_fixed_delta = (float (*)(void *))(base + rvas->time_fixed_delta);
    time_set_fixed_delta = (void (*)(float, void *))(base + rvas->time_set_fixed_delta);
    time_frame_count = (int (*)(void *))(base + rvas->time_frame_count);
    fixed_process_resume = (uintptr_t)(base + rvas->hook_fixedprocess + 16);
    battle_process = (uintptr_t)(base + rvas->battle_process);
    if (hook((uint32_t *)(base + rvas->hook_fixedprocess), kFixedProcessPrologue, fixed_process_hook)) return -1;
    return hook((uint32_t *)(base + rvas->hook_battlestep), kBattleStepCall, battle_step_hook);
}

static void *game_library;
static void *game_symbol(const char *name) { return dlsym(game_library, name); }
static void roulette_log(const char *message) { __android_log_print(ANDROID_LOG_INFO, "Bunker", "%s", message); }

// IronSource.showRewardedVideo starts "stp x20, x19, [sp, #-0x20]!; stp x29, x30, [sp, #0x10];
// add x29, sp, #0x10; adrp x20, ..."; the hook replaces the whole method.
static const uint32_t kShowRewardedVideo[4] = {0xa9be4ff4u, 0xa9017bfdu, 0x910043fdu, 0xd00237f4u};

// 【rev D·L3b】warning-only when hook_showrewardedvideo is 0 (JP unresolved) or mismatch.
static void hook_roulette_ads(uint8_t *base, const ClientRvas *rvas) {
    if (!rvas->hook_showrewardedvideo) {
        __android_log_print(ANDROID_LOG_WARN, "Bunker", "Special Gift Roulette: no %s RVA (unresolved); the video ad stays",
                            rvas == &kJpRvas ? "JP" : "EN");
        return;
    }
    if (roulette_ads_init(game_symbol, roulette_log, NULL) || hook((uint32_t *)(base + rvas->hook_showrewardedvideo), kShowRewardedVideo, (void (*)(void))roulette_ads_show))
        __android_log_print(ANDROID_LOG_WARN, "Bunker", "Special Gift Roulette: unsupported game binary; the video ad stays");
}

static const char *apply(int fps, int size, const char *declared_region,
                         const char *declared_package, char *message, size_t length) {
    Site list[8];
    void *library = dlopen("libil2cpp.so", RTLD_NOW);
    void *symbol = library ? dlsym(library, "il2cpp_init") : NULL;
    Dl_info info;
    if (!symbol || !dladdr(symbol, &info)) {
        snprintf(message, length, "Game library not found: %s", dlerror());
        return message;
    }
    uint8_t *base = info.dli_fbase;

    // 【rev D·L4】Region-consistency detection: the declared region and the
    // package name are cross-checked against the library file; any
    // contradiction or unknown client fails fast.
    const ClientFact *fact = detect_client(info.dli_fname, declared_region, declared_package);
    if (!fact) {
        snprintf(message, length, "Unsupported game binary: client detection refused libil2cpp.so (%s)", info.dli_fname ? info.dli_fname : "?");
        return message;
    }
    const ClientRvas *rvas = fact->rvas;
    __android_log_print(ANDROID_LOG_INFO, "Bunker",
                        "Display patch: %s table selected (package %s, libil2cpp.so %lld B)",
                        fact->region, fact->package, fact->lib_size);

    int count = sites(rvas, fps, size, list);
    game_library = library;
    hook_roulette_ads(base, rvas);

    // kSnapArrive: per-client RVA, same original/patched words.
    Site snap = {rvas->snap_arrive, kSnapArriveOriginal.original, kSnapArriveOriginal.patched};
    uint32_t *snap_addr = (uint32_t *)(base + snap.rva);
    if (*snap_addr == snap.original) {
        if (write_word_assert(snap_addr, snap.patched)) {
            snprintf(message, length, "Byte assertion failed at 0x%X after snap patch", snap.rva);
            return message;
        }
    } else if (*snap_addr != snap.patched)
        __android_log_print(ANDROID_LOG_WARN, "Bunker", "Snapping lists: unsupported game binary; summon buttons can stop answering above 30 fps");

    if (text_buffer_fix(base, write_word))
        __android_log_print(ANDROID_LOG_WARN, "Bunker", "Text builder: unsupported game binary; long texts can still overrun");

    const struct { uint32_t rva; const uint32_t *original; } hooks[] = {
        {rvas->hook_fixedprocess, kFixedProcessPrologue},
        {rvas->hook_battlestep, kBattleStepCall},
        {rvas->hook_changestate, kChangeState},
        {rvas->hook_triggerenter, kTriggerEnter}
    };
    // The event-zone hooks (2 and 3) go in at every frame rate; the frame-timing ones only above 30.
    for (int h = fps > 30 ? 0 : 2; h < 4; h++) {
        uint32_t *at = (uint32_t *)(base + hooks[h].rva);
        if (at[0] == 0x58000050u) continue;
        for (int i = 0; i < 4; i++) if (at[i] != hooks[h].original[i]) {
            snprintf(message, length, "Unsupported game binary at 0x%X; nothing changed", hooks[h].rva);
            return message;
        }
    }
    for (int i = 0; i < count; i++) {
        uint32_t now = *(uint32_t *)(base + list[i].rva);
        if (now != list[i].original && now != list[i].patched) {
            snprintf(message, length, "Unsupported game binary at 0x%X (found %08X); nothing changed", list[i].rva, now);
            return message;
        }
    }
    for (int i = 0; i < count; i++) {
        uint32_t *address = (uint32_t *)(base + list[i].rva);
        if (*address != list[i].patched) {
            int rc = write_word_assert(address, list[i].patched);
            if (rc == -1) {
                snprintf(message, length, "Could not write the game code at 0x%X", list[i].rva);
                return message;
            }
            if (rc == -2) {
                snprintf(message, length, "Byte assertion failed at 0x%X after patch", list[i].rva);
                return message;
            }
        }
    }
    if (hook_event_zones(base, rvas)) {
        snprintf(message, length, "Could not write the game's story-event code");
        return message;
    }
    if (fps > 30 && hook_frame_rate(base, rvas)) {
        snprintf(message, length, "Could not write the game's frame timing code");
        return message;
    }
    return "";
}

/** Applies the choices; 0 keeps the game's own value. Returns "" or an error.
 *  region (manifest org.veritr1x.bunker.REGION) and package_name feed the
 *  【rev D·L4】region-consistency detection; either may be empty when the
 *  build declares nothing. */
JNIEXPORT jstring JNICALL Java_org_veritr1x_bunker_DisplayPatch_apply(JNIEnv *env, jclass cls, jint fps, jint size,
                                                                     jstring region, jstring package_name) {
    (void)cls;
    char message[160];
    if ((fps && (fps < 30 || fps > 240)) || (size && (size < FullHD || size > DeviceMax)))
        return (*env)->NewStringUTF(env, "Unsupported display setting");
    const char *declared_region = region ? (*env)->GetStringUTFChars(env, region, NULL) : NULL;
    const char *declared_package = package_name ? (*env)->GetStringUTFChars(env, package_name, NULL) : NULL;
    const char *result = apply(fps, size, declared_region, declared_package, message, sizeof message);
    if (declared_region) (*env)->ReleaseStringUTFChars(env, region, declared_region);
    if (declared_package) (*env)->ReleaseStringUTFChars(env, package_name, declared_package);
    return (*env)->NewStringUTF(env, result);
}
