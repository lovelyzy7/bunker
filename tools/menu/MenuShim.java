package org.veritr1x.bunker;

import android.content.Context;
import android.os.Bundle;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;

/**
 * Starts the Mod Menu inside the game's process, then hands over to the game.
 *
 * The command-line injector writes this call into the game's smali; this
 * prebuilt subclass does the same through the manifest, so the in-browser
 * builder can add the menu without a dex compiler. The menu is optional: if it
 * cannot start, the game still does.
 */
public class MenuShim extends com.google.firebase.MessagingUnityPlayerActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        try {
            com.android.support.Main.Start(this);
        } catch (Throwable failed) {
            // No overlay permission, a menu that cannot load, anything else:
            // leave a note for support and play without it.
            note(this, "Mod Menu did not start: " + Log.getStackTraceString(failed));
        }
        super.onCreate(savedInstanceState);
    }

    /** The menu's own log lines are hidden on some builds; a file always survives. */
    private static void note(Context context, String message) {
        try {
            File folder = context.getFilesDir();
            FileOutputStream out = new FileOutputStream(new File(folder, "menushim.log"), true);
            out.write((System.currentTimeMillis() + " " + message + "\n").getBytes("UTF-8"));
            out.close();
        } catch (Throwable ignored) {
        }
    }
}
