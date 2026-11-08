package com.ganzx.floating;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.os.Build;
import android.os.IBinder;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.CookieManager;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class FloatingService extends Service {

    private WindowManager windowManager;
    private View panel;
    private WebView webView;
    private WindowManager.LayoutParams params;
    private boolean collapsed = false;

    private final String website =
        "https://ganz-x-ofc-fsgd0.faable.link";

    @Override
    public void onCreate() {
        super.onCreate();
        createNotification();
        showPanel();
    }

    private void createNotification() {
        String channelId = "ganz_floating";

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                channelId,
                "GANZ X Floating Panel",
                NotificationManager.IMPORTANCE_LOW
            );
            getSystemService(NotificationManager.class)
                .createNotificationChannel(channel);
        }

        Intent open = new Intent(this, MainActivity.class);
        PendingIntent pending = PendingIntent.getActivity(
            this, 0, open,
            PendingIntent.FLAG_UPDATE_CURRENT |
            PendingIntent.FLAG_IMMUTABLE
        );

        Notification notification = new Notification.Builder(this, channelId)
            .setContentTitle("GANZ X Floating Panel aktif")
            .setContentText("Panel Like Free Fire sedang berjalan")
            .setSmallIcon(android.R.drawable.ic_menu_view)
            .setContentIntent(pending)
            .setOngoing(true)
            .build();

        startForeground(1, notification);
    }

    private void showPanel() {
        windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(15, 18, 35));

        LinearLayout bar = new LinearLayout(this);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(10, 4, 6, 4);
        bar.setBackgroundColor(Color.rgb(35, 48, 100));

        TextView title = new TextView(this);
        title.setText("GANZ X - OFC");
        title.setTextColor(Color.WHITE);
        title.setTextSize(14);
        title.setPadding(4, 8, 4, 8);
        bar.addView(title, new LinearLayout.LayoutParams(
            0, -2, 1
        ));

        Button minimize = new Button(this);
        minimize.setText("—");
        bar.addView(minimize);

        Button close = new Button(this);
        close.setText("X");
        bar.addView(close);

        root.addView(bar, new LinearLayout.LayoutParams(
            -1, dp(44)
        ));

        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setLoadsImagesAutomatically(true);
        settings.setSupportZoom(false);
        settings.setAllowFileAccess(false);

        CookieManager.getInstance().setAcceptCookie(true);
        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient());
        webView.loadUrl(website);

        root.addView(webView, new LinearLayout.LayoutParams(
            -1, 0, 1
        ));

        params = new WindowManager.LayoutParams(
            getResources().getDisplayMetrics().widthPixels - dp(24),
            dp(480),
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL |
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        );

        params.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL;
        params.y = dp(90);

        panel = root;
        windowManager.addView(panel, params);

        minimize.setOnClickListener(v -> {
            collapsed = !collapsed;
            webView.setVisibility(collapsed ? View.GONE : View.VISIBLE);
            params.height = collapsed ? dp(48) : dp(480);
            windowManager.updateViewLayout(panel, params);
            minimize.setText(collapsed ? "□" : "—");
        });

        close.setOnClickListener(v -> stopSelf());

        bar.setOnTouchListener(new View.OnTouchListener() {
            private int startX, startY;
            private float touchX, touchY;

            @Override
            public boolean onTouch(View view, MotionEvent event) {
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        startX = params.x;
                        startY = params.y;
                        touchX = event.getRawX();
                        touchY = event.getRawY();
                        return true;

                    case MotionEvent.ACTION_MOVE:
                        params.x = startX + (int)(event.getRawX() - touchX);
                        params.y = startY + (int)(event.getRawY() - touchY);
                        windowManager.updateViewLayout(panel, params);
                        return true;
                }
                return false;
            }
        });
    }

    private int dp(int value) {
        return (int)(value * getResources().getDisplayMetrics().density);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        if (panel != null && windowManager != null) {
            windowManager.removeView(panel);
            panel = null;
        }
        if (webView != null) {
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
