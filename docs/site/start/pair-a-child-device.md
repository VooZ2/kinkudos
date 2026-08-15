# Pair a child device

A child profile and a child device are different. The profile holds the child’s name, PIN, rules, and history. Pairing authorises one specific browser, phone, tablet, or installed PWA to show profiles and accept a child PIN.

## Pair the device you are using now

1. Sign in as a parent on the device that the child will use.
2. Open **Parents → Settings → Child devices**.
3. Enter a clear **Device name**, for example “Kitchen tablet”.
4. Select **Allow on this device**.
5. Sign out or open the child sign-in page. The child can now select their profile and enter their four-digit PIN.

## Pair another device with a private link

1. On any signed-in parent device, open **Parents → Settings → Child devices**.
2. Select **Send a link**. KinKudos opens a share dialog with the private URL.
3. Use **Copy** or **Share…**, then open the link on the intended device. Do not post it in a group chat or leave it in a shared note.
4. The link pairs that device once, then expires after **10 minutes**. The child can select their profile and enter their PIN.

After pairing, KinKudos shows a confirmation such as **This device is paired as
Mac · Chrome**. If no custom name was entered, the confirmation and device list
use an automatically assigned broad device summary.

<img class="screenshot-image" src="../../assets/device-pairing-success-26-6-4.png" alt="Pairing success message on the child profile screen" loading="lazy">

The screenshot uses fictional demonstration data.

## Manage paired devices

The device list shows a broad device icon, an optional custom name, a summary
such as **iPhone · Safari** or **Android tablet · Chrome**, a stable six-character
ID, and when the device was last used. The classification covers phone, tablet,
computer, and unknown device categories; it does not promise an exact model.
Devices unused for 30 days are hidden from this list automatically (pairing is
not revoked). They reappear when the device is used again. **Revoke all child
devices** still covers every non-revoked pairing, including hidden ones.

Rename entries so you can recognise them. On mobile, **Revoke** is shown as a
compact trash-can icon. Select it immediately if a device is lost, sold, lent
long-term, or no longer belongs to the family. Revoking removes child access and
child notifications on that device; it does not delete the child profile or
their history.

An actively used paired device has its access cookie renewed, so active pairing
should not quietly expire. Revocation still invalidates the device immediately;
it must be paired again before sign-in.

The parent administrator can choose **Revoke all child devices** after entering their password. This is useful after a broad security concern, but every child browser/PWA must then be paired again.

[Accounts and devices →](../security/accounts-and-devices.md) · [PINs and sign-in protection →](../security/pin-and-sign-in.md) · [Lietuviškai](pair-a-child-device.lt.md)
