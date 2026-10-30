package org.veritr1x.bunker;

import android.content.Context;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import org.json.JSONObject;
import java.util.Locale;

/** Which game release this build targets: "en" (全球服) or "jp" (日服). */
final class Region {
    private Region() {}

    /**
     * build.json written by the builder is the source of truth; the manifest
     * meta-data covers builds made before it, and "en" is the safe default.
     */
    static String of(Context context) {
        JSONObject build = Updater.installedBuild(context);
        String region = build == null ? "" : build.optString("region", "").trim();
        if (region.isEmpty()) {
            try {
                ApplicationInfo info = context.getPackageManager()
                        .getApplicationInfo(context.getPackageName(), PackageManager.GET_META_DATA);
                if (info.metaData != null) {
                    String declared = info.metaData.getString("org.veritr1x.bunker.REGION");
                    if (declared != null) region = declared.trim();
                }
            } catch (PackageManager.NameNotFoundException ignored) {
                // fall through to the default
            }
        }
        return region.isEmpty() ? "en" : region.toLowerCase(Locale.ROOT);
    }

    /**
     * The build's own region declaration — build.json first, then the manifest
     * meta-data — or "" when neither is present. Unlike of() this never
     * defaults: display_patch.c cross-checks the declaration against the
     * game library and must fail fast instead of guessing.
     */
    static String declared(Context context) {
        JSONObject build = Updater.installedBuild(context);
        String region = build == null ? "" : build.optString("region", "").trim();
        if (region.isEmpty()) {
            try {
                ApplicationInfo info = context.getPackageManager()
                        .getApplicationInfo(context.getPackageName(), PackageManager.GET_META_DATA);
                if (info.metaData != null) {
                    String value = info.metaData.getString("org.veritr1x.bunker.REGION");
                    if (value != null) region = value.trim();
                }
            } catch (PackageManager.NameNotFoundException ignored) {
                // fall through: no declaration
            }
        }
        return region.toLowerCase(Locale.ROOT);
    }

    /** The text/voice folder the Archive and the name extractor read. */
    static String language(String region) {
        return "jp".equals(region) ? "ja" : "en";
    }
}
