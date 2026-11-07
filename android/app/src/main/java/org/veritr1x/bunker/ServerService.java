package org.veritr1x.bunker;

import android.app.*;
import android.content.*;
import android.content.pm.ServiceInfo;
import android.net.Uri;
import android.os.*;
import org.json.JSONObject;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class ServerService extends Service {
    static final String START="start", STOP="stop", ASSETS="assets", MASTER="master", BACKUP="backup", TOOLS="tools", CLOSE_TOOLS="close_tools", SAVE="save", ARCHIVE="archive", LINK="link";
    static volatile boolean running=false, busy=false, tools=false;
    // Pod Programs opened beside the running game, which it has not closed yet. Cleared only once
    // the server is stopped and the save backed up, so a failed backup leaves changes refused.
    static volatile boolean toolsBesideGame=false;
    // Import progress, 0-1000, or -1 when there is no measured copy in progress.
    static volatile int permille=-1;
    static volatile String state="Server stopped", detail="Import your game files to get started.";
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private final Handler main=new Handler(Looper.getMainLooper());
    private volatile boolean cancelled=false;
    private PowerManager.WakeLock wake;
    private long lastNotification;
    // The running service, for Pod Programs' Python (closeGameForTools).
    private static volatile ServerService instance;
    private final Runnable monitor=new Runnable() { public void run() {
        if(!running) return;
        try {
            JSONObject s=new JSONObject(NativeBridge.status());
            if(s.getString("state").equals("error")) {
                running=false; state="Server stopped"; detail=s.optString("error"); finishForeground(); return;
            }
        } catch(Exception ignored) {}
        main.postDelayed(this,2000);
    }};
    @Override public void onCreate() {
        super.onCreate();
        NativeBridge.setLogDir(FilesStore.logs(this).getAbsolutePath());NativeBridge.setBackupDir(new java.io.File(new java.io.File(getFilesDir(),"tools"),"backups").getAbsolutePath());
        NotificationChannel channel=new NotificationChannel("server",Text.of("Local game server"),NotificationManager.IMPORTANCE_LOW);
        channel.setDescription(Text.of("Server status and Stop control while you play."));
        getSystemService(NotificationManager.class).createNotificationChannel(channel);
        wake=((PowerManager)getSystemService(POWER_SERVICE)).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,"lunartear:server");
        wake.setReferenceCounted(false);
    }
    /** The state as the player reads it; the launcher compares the raw values. */
    private static String shown(String state){
        switch(state){
            case "Server running": return Text.of("Running");
            case "Server stopped": return Text.of("Stopped");
            case "Starting server": return Text.of("Starting");
            case "Preparing tools": return Text.of("Opening Pod Programs");
            case "Tools ready": return Text.of("Pod Programs open");
            default: return Text.of(state);
        }
    }
    private Notification notification() {
        PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class).putExtra("manage",true).addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        PendingIntent stop=PendingIntent.getService(this,1,new Intent(this,ServerService.class).setAction(STOP),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        Notification.Builder builder=new Notification.Builder(this,"server").setSmallIcon(Look.emblem(this)).setContentTitle("Lunar Tear · "+shown(state))
            .setContentText(Text.of(detail)).setContentIntent(open).setOngoing(true).setOnlyAlertOnce(true)
            .addAction(new Notification.Action.Builder(null,busy?Text.of("Cancel"):Text.of("Stop"),stop).build());
        if(busy&&permille>=0)builder.setProgress(1000,permille,false).setStyle(new Notification.BigTextStyle().bigText(detail));
        return builder.build();
    }
    private void update(String message) {
        detail=message;
        long now=SystemClock.elapsedRealtime();
        if(now-lastNotification>1000) { lastNotification=now; getSystemService(NotificationManager.class).notify(1,notification()); }
    }
    @Override public int onStartCommand(Intent intent,int flags,int startId) {
        if(intent==null) { stopSelf(); return START_NOT_STICKY; }
        String action=intent.getAction();
        if(TOOLS.equals(action)) {
            if(tools||busy)return START_NOT_STICKY;
            // With the game running, Pod Programs opens beside it; the first change that
            // needs the game closed closes it then (closeGameForTools).
            final boolean live=running;
            toolsBesideGame=live;
            toolsPaused=false;toolsBackedUp=false;
            tools=true;busy=true;cancelled=false;state="Preparing tools";detail=live?"Opening Pod Programs…":"Stopping the game…";
            if(Build.VERSION.SDK_INT>=34)startForeground(1,notification(),ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
            else startForeground(1,notification());
            wake.acquire(12*60*60*1000L);
            if(!live)main.removeCallbacks(monitor);
            worker.execute(()->{
                try {
                    if(!live)stopGameForTools();
                    ToolsRuntime.start(this,this::update);
                    if(cancelled){ToolsRuntime.stop();tools=false;state=running?"Server running":"Server stopped";}
                    else {state="Tools ready";detail=running?"The game is still running. Changes to your save close it first.":"Close Pod Programs to return to the game.";}
                } catch(Exception|LinkageError error) {
                    tools=false;state="Needs attention";detail=error.getMessage()==null?error.toString():error.getMessage();
                    android.util.Log.e("LunarTear",Text.of("Tools startup failed"),error);
                } finally {
                    busy=false;
                    if(tools)getSystemService(NotificationManager.class).notify(1,notification());else finishForeground();
                }
            });
            return START_NOT_STICKY;
        }
        if(CLOSE_TOOLS.equals(action)&&running&&toolsBesideGame) {
            // The game was never closed: Pod Programs closes and the game plays on.
            busy=true;state="Closing Pod Programs";detail="The game keeps running.";
            worker.execute(()->{
                try {ToolsRuntime.stop();tools=false;toolsBesideGame=false;state="Server running";detail="Ready to play";}
                catch(Exception error){state="Needs attention";detail=error.getMessage();}
                finally {busy=false;}
            });
            return START_NOT_STICKY;
        }
        if(STOP.equals(action)||CLOSE_TOOLS.equals(action)) {
            cancelled=true;
            state="Stopping"; detail="Finishing the current operation and saving progress…";
            busy=true;
            worker.execute(()->{
                try {ToolsRuntime.stop();tools=false;NativeBridge.stop();running=false;state="Server stopped";detail="Your saves are stored on this phone.";}
                catch(Exception error){state="Needs attention";detail=error.getMessage();}
                finally {busy=false;if(!tools)finishForeground();}
            });
            return START_NOT_STICKY;
        }
        if(busy||running||tools) return START_NOT_STICKY;
        busy=true; cancelled=false; permille=-1;
        state=START.equals(action)?"Starting server":BACKUP.equals(action)?"Exporting saves":SAVE.equals(action)?"Importing save":"Importing files";
        detail=START.equals(action)?Text.of("Loading game data…"):Text.of("Keep the source files available until this finishes.");
        if(Build.VERSION.SDK_INT>=34) startForeground(1,notification(),ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
        else startForeground(1,notification());
        wake.acquire(12*60*60*1000L);
        Uri uri=intent.getData();
        worker.execute(()->{
            try {
                FilesStore.recover(this);
                if(START.equals(action)) {
                    FilesStore.ensureBootstrap(this);
                    String error=NativeBridge.setPortOffset(Ports.offset(this));
                    if(error==null||!error.isEmpty()) throw new IllegalStateException(error==null?Text.of("Native server did not respond"):error);
                    error=NativeBridge.start(FilesStore.data(this).getAbsolutePath(),FilesStore.root(this).getAbsolutePath());
                    if(error==null||!error.isEmpty()) throw new IllegalStateException(error==null?Text.of("Native server did not respond"):error);
                    if(cancelled) { NativeBridge.stop(); throw new InterruptedException(Text.of("Start cancelled")); }
                    // Confirm the game can reach this server on every port before playing.
                    String failure=selfTestFailure(NativeBridge.selfTest());
                    if(failure!=null) { NativeBridge.stop(); throw new IllegalStateException(failure); }
                    running=true;state="Server running";
                    detail="Ready to play";
                    main.post(monitor);
                } else {
                    FilesStore.Progress progress=new FilesStore.Progress(){
                        public void update(String text){ServerService.this.update(text);}
                        public boolean cancelled(){return cancelled;}
                        public void fraction(int value){permille=value;}
                    };
                    if(ASSETS.equals(action)) FilesStore.importAssets(this,uri,progress);
                    else if(ARCHIVE.equals(action)) FilesStore.importArchive(this,uri,progress);
                    else if(LINK.equals(action)) FilesStore.linkAssets(this,uri,progress);
                    else if(MASTER.equals(action)) FilesStore.importMaster(this,uri,progress);
                    else if(BACKUP.equals(action)) FilesStore.backup(this,uri);
                    else if(SAVE.equals(action)) { FilesStore.importSave(this,uri); closeGame(); }
                    else throw new IllegalArgumentException(Text.of("Unknown operation"));
                    state=BACKUP.equals(action)?Text.of("Saves exported"):SAVE.equals(action)?Text.of("Save imported"):Text.of("Import complete");
                    detail=BACKUP.equals(action)?Text.of("Keep your backup somewhere safe."):SAVE.equals(action)?Text.of("Save imported. Tap Play to continue with it."):FilesStore.ready(this)?Text.of("Your files are ready. Start the server when you want to play."):Text.of("Import the remaining game files to continue.");
                }
            } catch(Exception|LinkageError error) {
                running=false;state=cancelled?Text.of("Operation cancelled"):Text.of("Needs attention");
                detail=error.getMessage()==null?error.toString():error.getMessage();
                android.util.Log.e("LunarTear",detail,error);
            } finally {
                busy=false; permille=-1;
                if(running) getSystemService(NotificationManager.class).notify(1,notification());
                else finishForeground();
            }
        });
        return START_NOT_STICKY;
    }
    // The launcher, Tools and this service share a process apart from the game.
    // Close the paused Unity process so its cached save/master cannot survive
    // the change.
    /** Stops the server, backs up the save and closes the game, before Pod Programs changes them. */
    private void stopGameForTools() {
        main.removeCallbacks(monitor);
        NativeBridge.stop();running=false;
        String error=NativeBridge.prepareBackup(FilesStore.data(this).getAbsolutePath());
        if(!error.isEmpty())throw new IllegalStateException(error);
        closeGame();
    }
    /** Pod Programs: whether the game and its server are still running beside it. */
    public static boolean gameLive(){return tools&&toolsBesideGame;}
    /** Pod Programs, before a change to the save or the game's data: closes the game. Returns "" or why not. */
    public static String closeGameForTools(){
        ServerService service=instance;
        if(service==null)return "The Bunker's service is not running";
        synchronized(ServerService.class){
            if(!toolsBesideGame)return "";
            try {
                state="Preparing tools";detail="Stopping the game…";
                service.stopGameForTools();
                toolsBesideGame=false;
                state="Tools ready";detail="Close Pod Programs to return to the game.";
                return "";
            } catch(Exception|LinkageError error) {
                android.util.Log.e("LunarTear","Closing the game for Pod Programs failed",error);
                return error.getMessage()==null?error.toString():error.getMessage();
            }
        }
    }
    // Pod Programs beside the game: a change to the save or the game's data
    // stops the server for the change (pauseForTools) and starts it again
    // after (resumeForTools), which sends the game back to its title screen to
    // sign in again and load it. The game keeps running throughout.
    private static boolean toolsPaused=false, toolsBackedUp=false;
    /** Pod Programs, before a change beside the running game: stops the server, backing the save up once. Returns "" or why not. */
    public static String pauseForTools(){
        ServerService service=instance;
        if(service==null)return "The Bunker's service is not running";
        synchronized(ServerService.class){
            if(!toolsBesideGame||toolsPaused)return "";
            service.main.removeCallbacks(service.monitor);
            NativeBridge.stop();running=false;
            if(!toolsBackedUp){
                String error=NativeBridge.prepareBackup(FilesStore.data(service).getAbsolutePath());
                if(!error.isEmpty()){
                    // Nothing was changed yet: the game plays on as it was, if its server starts again.
                    String restart=resumeServer(service);
                    if(restart.isEmpty())return error;
                    // It cannot reach a server: close it, as resumeForTools does.
                    android.util.Log.e("LunarTear","Restarting the server beside the game failed: "+restart);
                    toolsBesideGame=false;service.closeGame();
                    state="Tools ready";detail="Close Pod Programs to return to the game.";
                    return error+" The game was closed: tap Deploy to play again.";
                }
                toolsBackedUp=true;
            }
            toolsPaused=true;state="Applying a change";detail="The game returns to its title screen to load it.";
            return "";
        }
    }
    /** Pod Programs, after a change beside the running game: starts the server and sends the game to its title screen. Returns "" or why not. */
    public static String resumeForTools(){return resumeForTools(true);}
    /** As resumeForTools; title false for a change that was refused or changed nothing, so the game keeps its place. */
    public static String resumeForTools(boolean title){
        ServerService service=instance;
        if(service==null)return "The Bunker's service is not running";
        synchronized(ServerService.class){
            if(!toolsPaused)return "";
            toolsPaused=false;
            String error=resumeServer(service);
            if(error.isEmpty()){
                if(title){NativeBridge.requestTitle();state="Tools ready";detail="The game returns to its title screen to load your change.";}
                else{state="Tools ready";detail="Nothing changed; the game plays on.";}
                return "";
            }
            // The game cannot reach a server: close it, as before this change could run beside it.
            android.util.Log.e("LunarTear","Restarting the server beside the game failed: "+error);
            toolsBesideGame=false;service.closeGame();
            state="Tools ready";detail="Close Pod Programs to return to the game.";
            return error;
        }
    }
    private static String resumeServer(ServerService service){
        String error=NativeBridge.start(FilesStore.data(service).getAbsolutePath(),FilesStore.root(service).getAbsolutePath());
        if(error==null||!error.isEmpty())return error==null?"Native server did not respond":error;
        String failure=selfTestFailure(NativeBridge.selfTest());
        if(failure!=null){NativeBridge.stop();return failure;}
        running=true;service.main.post(service.monitor);
        return "";
    }
    private void closeGame() {
        ActivityManager manager=getSystemService(ActivityManager.class);
        for(ActivityManager.RunningAppProcessInfo process:manager.getRunningAppProcesses())
            if(process.uid==android.os.Process.myUid()&&process.pid!=android.os.Process.myPid()&&process.processName.equals(getPackageName()))android.os.Process.killProcess(process.pid);
    }
    /** Returns a message naming each port that failed the self-test, or null when all passed. */
    static String selfTestFailure(String report) {
        try {
            JSONObject r=new JSONObject(report);
            if(r.optBoolean("ok")) return null;
            StringBuilder text=new StringBuilder(Text.of("The game could not reach its server:"));
            org.json.JSONArray checks=r.getJSONArray("checks");
            for(int i=0;i<checks.length();i++){
                JSONObject c=checks.getJSONObject(i);
                if(!c.optBoolean("ok")) text.append("\n• Port ").append(c.optInt("port")).append(" (").append(c.optString("name")).append("): ").append(c.optString("detail"));
            }
            return text.toString();
        } catch(Exception e) { return Text.of("Server check failed: ")+e.getMessage(); }
    }
    private void finishForeground() {
        if(wake!=null&&wake.isHeld())wake.release();
        stopForeground(STOP_FOREGROUND_REMOVE);
        stopSelf();
    }
    @Override public void onDestroy() {
        if(instance==this)instance=null;
        cancelled=true;main.removeCallbacks(monitor);
        if(wake!=null&&wake.isHeld()) wake.release();
        // Never block the main thread waiting for Go's graceful shutdown.
        worker.execute(()->{if(tools){ToolsRuntime.stop();tools=false;}if(running){NativeBridge.stop();running=false;state="Server stopped";}busy=false;});
        worker.shutdown();
        stopForeground(STOP_FOREGROUND_REMOVE);
        super.onDestroy();
    }
    private final Messenger messenger=new Messenger(new Handler(Looper.getMainLooper(),message->{
        if(message.replyTo!=null) {
            Message reply=Message.obtain(null,message.what);
            Bundle b=new Bundle();b.putBoolean("running",running);b.putBoolean("busy",busy);b.putBoolean("tools",tools);b.putInt("permille",permille);b.putString("state",state);b.putString("detail",detail);
            if(message.what==2) { try { b.putString("native",NativeBridge.status()); } catch(Throwable e){b.putString("native","{\"logs\":\"Native server unavailable\"}");} }
            if(message.what==3) {
                // The checks take up to a few seconds; answer from a background thread.
                Messenger to=message.replyTo;
                new Thread(()->{
                    Bundle result=new Bundle();
                    try { result.putString("selftest",running?NativeBridge.selfTest():""); } catch(Throwable e){ result.putString("selftest",""); }
                    Message answer=Message.obtain(null,3);answer.setData(result);
                    try{to.send(answer);}catch(RemoteException ignored){}
                },"lunar-self-test").start();
                return true;
            }
            reply.setData(b);try{message.replyTo.send(reply);}catch(RemoteException ignored){}
        }
        return true;
    }));
    @Override public IBinder onBind(Intent intent){return messenger.getBinder();}
}
