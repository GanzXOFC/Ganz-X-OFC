package com.ganzx.floating;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Outline;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.view.ViewOutlineProvider;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {

    private LinearLayout toggleButton;
    private TextView toggleIcon;
    private TextView toggleLabel;

    private int dp(int value) {
        return (int) (value *
            getResources().getDisplayMetrics().density);
    }

    private TextView makeText(String value, int size, int color) {
        TextView text = new TextView(this);
        text.setText(value);
        text.setTextSize(size);
        text.setTextColor(color);
        text.setGravity(Gravity.CENTER);
        return text;
    }

    private Button makeButton(String value, int color) {
        Button button = new Button(this);
        button.setText(value);
        button.setTextColor(Color.WHITE);
        button.setTextSize(14);
        button.setAllCaps(false);
        button.setBackgroundTintList(
            android.content.res.ColorStateList.valueOf(color)
        );
        return button;
    }

    private void updateToggleButton(boolean running) {
        if (toggleIcon == null || toggleLabel == null) return;

        toggleLabel.setText(running ? "MATIKAN" : "HIDUPKAN");
        toggleIcon.setTextColor(
            running ? 0xFFFF4545 : 0xFF39E879
        );
    }

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

        updateToggleButton(true);
    }

    private void togglePanelService() {
        if (FloatingService.isRunning) {
            stopService(new Intent(this, FloatingService.class));
            updateToggleButton(false);
        } else {
            startPanel();
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        updateToggleButton(FloatingService.isRunning);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);
        layout.setPadding(dp(24), dp(24), dp(24), dp(24));
        layout.setBackgroundColor(Color.rgb(16, 20, 38));

        ImageView profile = new ImageView(this);

        int imageId = getResources().getIdentifier(
            "ic_launcher", "mipmap", getPackageName()
        );

        if (imageId != 0) {
            profile.setImageResource(imageId);
        } else {
            profile.setImageResource(getApplicationInfo().icon);
        }

        GradientDrawable circle = new GradientDrawable();
        circle.setShape(GradientDrawable.OVAL);
        circle.setColor(Color.WHITE);
        profile.setBackground(circle);
        profile.setClipToOutline(true);
        profile.setScaleType(ImageView.ScaleType.CENTER_CROP);
        profile.setOutlineProvider(new ViewOutlineProvider() {
            @Override
            public void getOutline(View view, Outline outline) {
                outline.setOval(
                    0, 0, view.getWidth(), view.getHeight()
                );
            }
        });

        LinearLayout.LayoutParams photoParams =
            new LinearLayout.LayoutParams(dp(112), dp(112));
        photoParams.bottomMargin = dp(16);
        layout.addView(profile, photoParams);

        TextView title = makeText(
            "Caca", 29, Color.WHITE
        );
        title.setTypeface(null, 1);
        layout.addView(title);

        TextView subtitle = makeText(
            "Like Free Fire", 17, 0xFFB9C9FF
        );
        LinearLayout.LayoutParams subParams =
            new LinearLayout.LayoutParams(-1, -2);
        subParams.topMargin = dp(5);
        subParams.bottomMargin = dp(22);
        layout.addView(subtitle, subParams);

        TextView important = makeText(
            "PENTING : 100% aman karena ini website Like Free Fire " +
            "versi mengambang, tidak ada sangkutan nya ke aplikasi lainnya.",
            14, 0xFFE0E5FF
        );
        important.setGravity(Gravity.CENTER);
        important.setPadding(dp(8), dp(12), dp(8), dp(12));

        GradientDrawable infoBackground = new GradientDrawable();
        infoBackground.setColor(0xFF202A4B);
        infoBackground.setCornerRadius(dp(12));
        important.setBackground(infoBackground);

        LinearLayout.LayoutParams infoParams =
            new LinearLayout.LayoutParams(-1, -2);
        infoParams.bottomMargin = dp(22);
        layout.addView(important, infoParams);

        toggleButton = new LinearLayout(this);
        toggleButton.setOrientation(LinearLayout.HORIZONTAL);
        toggleButton.setGravity(Gravity.CENTER);
        toggleButton.setPadding(dp(18), 0, dp(18), 0);

        GradientDrawable toggleBackground = new GradientDrawable(
            GradientDrawable.Orientation.LEFT_RIGHT,
            new int[] {0xFF174DCE, 0xFF123CB5}
        );
        toggleBackground.setCornerRadius(dp(18));
        toggleButton.setBackground(toggleBackground);
        toggleButton.setElevation(dp(5));
        toggleButton.setClickable(true);
        toggleButton.setFocusable(true);

        toggleIcon = makeText("⏻", 40, 0xFF39E879);
        toggleIcon.setTypeface(null, 1);
        toggleButton.addView(toggleIcon, new LinearLayout.LayoutParams(
            dp(75), -1
        ));

        View toggleDivider = new View(this);
        toggleDivider.setBackgroundColor(0xCCFFFFFF);
        toggleButton.addView(toggleDivider, new LinearLayout.LayoutParams(
            dp(2), dp(36)
        ));

        toggleLabel = makeText("", 19, Color.WHITE);
        toggleLabel.setTypeface(null, 1);
        LinearLayout.LayoutParams labelParams =
            new LinearLayout.LayoutParams(0, -1, 1);
        toggleButton.addView(toggleLabel, labelParams);

        updateToggleButton(FloatingService.isRunning);
        toggleButton.setOnClickListener(v -> togglePanelService());

        LinearLayout.LayoutParams toggleParams =
            new LinearLayout.LayoutParams(-1, dp(64));
        layout.addView(toggleButton, toggleParams);

        LinearLayout stop = new LinearLayout(this);
        stop.setOrientation(LinearLayout.HORIZONTAL);
        stop.setGravity(Gravity.CENTER);
        stop.setPadding(dp(18), 0, dp(18), 0);

        GradientDrawable stopBackground = new GradientDrawable(
            GradientDrawable.Orientation.LEFT_RIGHT,
            new int[] {0xFF30364B, 0xFF252B40}
        );
        stopBackground.setCornerRadius(dp(18));
        stop.setBackground(stopBackground);
        stop.setElevation(dp(3));

        TextView stopIcon = makeText("×", 30, 0xFF252B40);
        stopIcon.setTypeface(null, 1);

        GradientDrawable stopCircle = new GradientDrawable();
        stopCircle.setShape(GradientDrawable.OVAL);
        stopCircle.setColor(Color.WHITE);
        stopIcon.setBackground(stopCircle);

        stop.addView(stopIcon, new LinearLayout.LayoutParams(
            dp(42), dp(42)
        ));

        View stopDivider = new View(this);
        stopDivider.setBackgroundColor(0xCCFFFFFF);
        LinearLayout.LayoutParams stopDividerParams =
            new LinearLayout.LayoutParams(dp(2), dp(36));
        stopDividerParams.leftMargin = dp(18);
        stopDividerParams.rightMargin = dp(18);
        stop.addView(stopDivider, stopDividerParams);

        TextView stopLabel = makeText("TUTUP", 19, Color.WHITE);
        stopLabel.setTypeface(null, 1);
        stop.addView(stopLabel, new LinearLayout.LayoutParams(
            0, -1, 1
        ));

        stop.setClickable(true);
        stop.setFocusable(true);
        stop.setOnClickListener(v -> {
            stopService(new Intent(this, FloatingService.class));
            finish();
        });

        LinearLayout.LayoutParams stopParams =
            new LinearLayout.LayoutParams(-1, dp(64));
        stopParams.topMargin = dp(10);
        layout.addView(stop, stopParams);

        setContentView(layout);
    }
}
