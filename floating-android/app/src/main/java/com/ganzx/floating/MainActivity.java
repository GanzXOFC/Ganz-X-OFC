package com.ganzx.floating;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {

    private void startPanel() {
        if (!Settings.canDrawOverlays(this)) {
            Intent intent = new Intent(
                Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:" + getPackageName())
            );
            startActivity(intent);
            return;
        }

        Intent service = new Intent(this, FloatingService.class);
        startForegroundService(service);
        finish();
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);
        layout.setPadding(28, 28, 28, 28);
        layout.setBackgroundColor(0xFF101426);

        TextView title = new TextView(this);
        title.setText("GANZ X - OFC");
        title.setTextSize(25);
        title.setTextColor(0xFFFFFFFF);
        title.setGravity(Gravity.CENTER);
        layout.addView(title);

        TextView info = new TextView(this);
        info.setText(
            "FLOATING LIKE FREE FIRE\n\n" +
            "Aktifkan izin Tampil di atas aplikasi lain, " +
            "lalu buka panel saat bermain Free Fire."
        );
        info.setTextColor(0xFFE0E5FF);
        info.setTextSize(15);
        info.setGravity(Gravity.CENTER);
        info.setPadding(0, 22, 0, 22);
        layout.addView(info);

        Button start = new Button(this);
        start.setText("AKTIFKAN PANEL MENGAMBANG");
        start.setOnClickListener(v -> startPanel());
        layout.addView(start);

        Button stop = new Button(this);
        stop.setText("TUTUP PANEL");
        stop.setOnClickListener(v ->
            stopService(new Intent(this, FloatingService.class))
        );
        layout.addView(stop);

        setContentView(layout);
    }
}
