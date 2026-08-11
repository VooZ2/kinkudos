# Notifications and installing KinKudos

KinKudos can be installed as an app-like PWA and can send browser notifications. Both are optional, and both are configured separately on each phone, tablet, computer, or browser.

## Install KinKudos

Installing gives KinKudos its own home-screen or app icon and is required for notifications on iPhone and iPad.

- **iPhone / iPad:** open KinKudos in Safari, choose **Share**, then **Add to Home Screen**. Open the installed app at least once before enabling notifications.
- **Android:** open the site in Chrome, use the browser menu, then choose **Install app** or **Add to Home screen**.
- **Computer:** in Chrome or Edge, use the install icon in the address bar or the browser menu’s **Install** option.

## Enable notifications

Sign in on the device, then select the bell icon in the top bar and accept the browser permission prompt. Repeat this for each device that should receive notifications. An active parent receives alerts for child submissions, reward requests, suggestions, and birthday-change requests; a child receives relevant parent decisions, assigned work, gifts, birthday awards, and an optional lottery reminder. Deactivating a parent removes that account's push subscriptions, so it no longer receives parent notifications.

The browser subscription must use a normal public HTTPS Web Push endpoint. Obvious invalid, local, private, or non-HTTPS endpoints are rejected. If the bell reports that notifications cannot be enabled, check browser/site notification permissions, open the installed PWA on iPhone/iPad, make sure the device has internet access, and retry from the public HTTPS address. Revoking a child device removes its child notification subscription. Notifications are a convenience, so always check the app itself for the current state.
