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

    private static final String ACTION_HIDE =
        "com.ganzx.floating.HIDE";
    private static final String ACTION_SHOW =
        "com.ganzx.floating.SHOW";

    private WindowManager windowManager;
    private LinearLayout root;
    private WebView webView;
    private WindowManager.LayoutParams params;
    private Button toggleButton;

    private boolean collapsed = true;
    private boolean panelAdded = false;

    private final String website =
        "https://ganz-x-ofc-fsgd0.faable.link";

    @Override
    public void onCreate() {
        super.onCreate();

        windowManager = (WindowManager)
            getSystemService(WINDOW_SERVICE);

        createNotification();
        showPanel();
    }

    private PendingIntent serviceIntent(String action, int code) {
        Intent intent = new Intent(this, FloatingService.class);
        intent.setAction(action);

        return PendingIntent.getService(
            this,
            code,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT |
            PendingIntent.FLAG_IMMUTABLE
        );
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

        Notification notification = new Notification.Builder(
            this, channelId
        )
            .setContentTitle("GANZ X Floating Panel")
            .setContentText("Panel Like Free Fire sedang berjalan")
            .setSmallIcon(android.R.drawable.ic_menu_view)
            .setContentIntent(pending)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .addAction(
                android.R.drawable.ic_menu_close_clear_cancel,
                "SEMBUNYIKAN PANEL",
                serviceIntent(ACTION_HIDE, 11)
            )
            .build();

        startForeground(1, notification);
    }

    private void updateNotification() {
        NotificationManager manager =
            getSystemService(NotificationManager.class);

        Notification.Builder builder;

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            builder = new Notification.Builder(this, "ganz_floating");
        } else {
            builder = new Notification.Builder(this);
        }

        Intent open = new Intent(this, MainActivity.class);

        PendingIntent pending = PendingIntent.getActivity(
            this, 0, open,
            PendingIntent.FLAG_UPDATE_CURRENT |
            PendingIntent.FLAG_IMMUTABLE
        );

        builder
            .setContentTitle("GANZ X Floating Panel")
            .setContentText(
                panelAdded
                    ? "Panel sedang tampil"
                    : "Panel disembunyikan sementara"
            )
            .setSmallIcon(android.R.drawable.ic_menu_view)
            .setContentIntent(pending)
            .setOngoing(true)
            .setOnlyAlertOnce(true);

        if (panelAdded) {
            builder.addAction(
                android.R.drawable.ic_menu_close_clear_cancel,
                "SEMBUNYIKAN PANEL",
                serviceIntent(ACTION_HIDE, 11)
            );
        } else {
            builder.addAction(
                android.R.drawable.ic_menu_view,
                "TAMPILKAN PANEL",
                serviceIntent(ACTION_SHOW, 12)
            );
        }

        manager.notify(1, builder.build());
    }

    private void showPanel() {
        if (panelAdded) return;

        root = new LinearLayout(this);
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

        bar.addView(title, new LinearLayout.LayoutParams(0, -2, 1));

        toggleButton = new Button(this);
        toggleButton.setText("□");
        bar.addView(toggleButton);

        Button close = new Button(this);
        close.setText("X");
        bar.addView(close);

        root.addView(bar, new LinearLayout.LayoutParams(-1, dp(48)));

        params = new WindowManager.LayoutParams(
            getResources().getDisplayMetrics().widthPixels - dp(24),
            dp(48),
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL |
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE |
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        );

        params.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL;
        params.y = dp(90);

        windowManager.addView(root, params);
        panelAdded = true;

        toggleButton.setOnClickListener(v -> togglePanel());
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
                        params.x = startX +
                            (int)(event.getRawX() - touchX);
                        params.y = startY +
                            (int)(event.getRawY() - touchY);
                        windowManager.updateViewLayout(root, params);
                        return true;

                    case MotionEvent.ACTION_UP:
                        return true;
                }
                return false;
            }
        });

        updateNotification();
    }

    private void hidePanel() {
        if (!panelAdded) return;

        removeWebView();

        if (root != null) {
            windowManager.removeView(root);
            root = null;
        }

        panelAdded = false;
        toggleButton = null;

        updateNotification();
    }

    private void togglePanel() {
        collapsed = !collapsed;

        if (collapsed) {
            removeWebView();
            params.height = dp(48);
            toggleButton.setText("□");
        } else {
            createWebView();
            params.height = dp(480);
            toggleButton.setText("—");
        }

        windowManager.updateViewLayout(root, params);
    }

    private void createWebView() {
        if (webView != null || root == null) return;

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

        root.addView(webView, new LinearLayout.LayoutParams(
            -1, 0, 1
        ));

        webView.loadUrl(website);
    }

    private void removeWebView() {
        if (webView == null) return;

        webView.stopLoading();
        webView.onPause();

        if (root != null) {
            root.removeView(webView);
        }

        webView.destroy();
        webView = null;
    }

    private int dp(int value) {
        return (int)(value *
            getResources().getDisplayMetrics().density);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && intent.getAction() != null) {
            if (ACTION_HIDE.equals(intent.getAction())) {
                hidePanel();
            } else if (ACTION_SHOW.equals(intent.getAction())) {
                showPanel();
            }
        }

        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        removeWebView();

        if (panelAdded && root != null) {
            windowManager.removeView(root);
            root = null;
            panelAdded = false;
        }

        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
