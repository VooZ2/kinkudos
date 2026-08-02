# Changelog

All notable project changes are documented in this file. The format follows
Keep a Changelog and versions use `YY.FEATURE.FIX`.

## [Unreleased]

### Added

- Public English-first user documentation now covers getting started, parent workflows, settings, security, maintenance, and quick help; Lithuanian equivalents are available from every section.
- Public security-reporting and release-support policies explain the private
  vulnerability channel, supported-version scope, and best-effort support
  boundaries.
- The hosted guide now offers an English/Lithuanian start path, focused parent
  workflows, and server-administration overviews for installation and recovery.
- Family administration, data limits, support boundaries, and private security
  reporting are now easier to find from the public guide.

### Changed

- Hosted documentation now uses the KinKudos icon, colour palette, typography, and light/dark appearance styling.

## [26.4.9] - 2026-07-31

### Fixed

- Public, sign-in, device-pairing, and first-time setup screens now share the
  colorful system shell and follow the device light or dark appearance until
  a signed-in parent or child interface takes over.

## [26.4.8] - 2026-07-31

### Added

- A small public installer can download and verify the latest release before
  starting the existing guided Docker Compose setup.

### Changed

- Published deployments now pull the versioned multi-platform application
  image from the public `vooz2/kinkudos` Docker Hub repository.

## [26.4.7] - 2026-07-31

### Changed

- Landing, parent sign-in, and password-reset screens now share a lighter,
  gradient-based visual design without additional image assets.
- The GitHub README now offers a visual product overview, demo-first onboarding,
  concise deployment guidance, and an optional VPS recommendation.
- The child lottery card and purchase dialog now use the clearer “Lottery tickets” label.

### Security

- Backup provider detection now parses the configured S3 repository hostname instead of matching an arbitrary URL substring.

## [26.4.6] - 2026-07-31

### Changed

- The README now links to the public demo and provides its parent and child
  sign-in details.

### Fixed

- Lithuanian feedback settings no longer imply a contrast between saving
  feedback and unavailable email notifications.

## [26.4.5] - 2026-07-31

### Fixed

- Parents now receive a Web Push notification when a child requests a reward.
- Web Push now also covers child suggestions and birthday-date change requests,
  along with the resulting parent decisions sent back to the child.

## [26.4.4] - 2026-07-31

### Changed

- Deployment documentation now covers preparing a fresh Ubuntu server with
  Docker Engine, Docker Compose, GitHub CLI, and a Caddy HTTPS proxy before
  running the KinKudos installer.

### Fixed

- Disabled IP restrictions now use the red inactive-state treatment, while
  enabled restrictions remain green.
- The feedback administration panel uses the same inner alignment as other
  settings panels and leaves consistent space below its explanation.
- Feedback screenshot controls inherit the shared interface typography instead
  of using the browser's mismatched default button font.

## [26.4.3] - 2026-07-31

### Fixed

- Child-device pairing links can now be confirmed in Safari without a CSRF
  403 response. The pairing page preserves the same-origin referrer Django
  requires while keeping the one-time token in the URL fragment.

## [26.4.2] - 2026-07-31

### Changed

- Network access settings now show a clear active state, explain which areas
  are IP-restricted, list the effective allowlist, and move editing into a
  focused dialog consistent with other service settings.
- Catalog titles explicitly use the shared system typography.

### Fixed

- The feedback administration panel no longer shows an unrelated public
  GitHub privacy warning.
- Footers now include a compact link for reporting a software bug.

## [26.4.1] - 2026-07-31

### Changed

- Parent and child request workflows use consistent icon-only actions for
  approval, completion, revision, rejection, cancellation, reward requests,
  and reward or goal proposals.
- Lithuanian settings and feedback wording is shorter and clearer.
- Deployment prerequisites no longer include a maintainer-specific registry
  login command or a release-specific migration notice.

### Fixed

- Workflow action icons keep matching state colors and stay on one row across
  parent and child layouts.
- Child-device pairing actions share one responsive two-column row without
  overlapping.
- The parent feedback panel uses compact privacy guidance and relies on the
  existing footer GitHub link instead of a large duplicate bug-report button.

## [26.4.0] - 2026-07-31

### Added

- Parents can pair each child browser or installed PWA with a one-time,
  short-lived link, review paired devices, rename them, and revoke one or all
  devices. A child PIN remains a second authentication step.
- Parents can optionally restrict child pages or the entire application to
  explicit IP addresses and CIDR networks. A server command can disable the
  restriction after accidental lockout.
- Production deployment supports host Nginx/Caddy, container-based proxies
  such as Nginx Proxy Manager, and Traefik without coupling the base Compose
  configuration to one proxy.
- Release tags publish one multi-platform GHCR application image for AMD64 and
  ARM64 installations.

### Changed

- Existing child profiles and PINs remain valid after upgrade, but every child
  browser or PWA must be paired once. Existing child push subscriptions are
  removed and must be enabled again on a paired device.
- In-app feedback is explicitly private family feedback, while software
  defects link to GitHub Issues with a warning not to include family data.
- Installation and updates validate the configured UID/GID ownership of
  writable host directories and pull the versioned application image.
- Scheduled maintenance also expires stale security counters, pairing links,
  and sessions.

### Security

- Parent login, password-reset, and child-PIN attempts are rate-limited using
  server-side database counters.
- Forwarded client IP headers are accepted only from configured trusted
  proxies, and the optional network allowlist uses the resulting verified
  client address.
- Child push subscriptions are bound to an approved device, pairing links are
  one-use and short-lived, and stored device credentials are hashed.
- The Django administration route is disabled by default in production.
- A regression test verifies that the generated VAPID private key is an actual
  usable EC private key.

## [26.3.2] - 2026-07-31

### Changed

- Settings use shorter section, field, and save-action wording in English and
  Lithuanian.
- The application footer links to the KinKudos GitHub repository.

### Fixed

- Family and per-child lottery checkboxes keep a consistent compact size and
  align correctly on desktop and mobile layouts.
- Child cards use consistent punctuation for the credit limit and weekly
  lottery status, with the credit-limit information icon closer to its label.

## [26.3.1] - 2026-07-31

### Changed

- Parents can configure the lottery ticket price and per-child weekly purchase
  limit, disable the lottery family-wide, and disable it for individual
  children. The family-wide switch has priority, while an already-open ticket
  remains available to finish.

### Fixed

- Task and reward catalog names plus parent action-dialog explanations now use
  the shared interface font consistently.
- Parent child cards show remaining weekly lottery tickets and use tighter
  spacing below the credit limit.
- The Lithuanian feedback email label uses shorter wording.

## [26.3.0] - 2026-07-30

### Added

- Children can buy a theme-aware scratch lottery ticket for 15 earned points,
  reveal a silver 3×3 number grid, and receive one matching positive, negative,
  or no-prize result. Tickets persist until completed, are limited to three per
  Monday–Sunday week, and never apply a loss below the child's credit floor.
- Eligible subscribed children who have at least 50 points and bought no ticket
  that week can receive one risk-transparent reminder at a random safe time in
  the second half of the week.
- Parents see read-only weekly ticket status plus separate ticket-cost and
  final-result ledger entries, without controls for the system reward.

## [26.2.2] - 2026-07-30

### Changed

- Parent catalog sections now stack vertically, task names use the shared
  system font, and Settings uses larger field labels with only titled group
  dividers.
- Child quick actions now use clearer icons and the order Completed task,
  Assign penalty, Assign tasks for today, Adjust points, and Change credit.
- Parent activity history now shows at most 50 actions from the last seven
  days, while append-only ledger records remain preserved.
- Recent backup actions now show no more than the latest five entries.
- Settings labels use shorter wording for task-photo points and retained
  feedback images.

### Fixed

- Saving general family settings now returns to the Settings section instead
  of opening the Home section.
- The credit-limit information icon is centered with its label.

## [26.2.1] - 2026-07-30

### Fixed

- Completed, cancelled, and expired assigned-task batches no longer show a
  misleading “Cancel remaining” action in parent history.

## [26.2.0] - 2026-07-30

### Added

- Parents can assign a daily list of catalog tasks and one custom task to a
  child from a new fifth quick action. Assigned values are snapshotted, expire
  at midnight, can be cancelled, and remain visible in parent history.
- Children see assigned work as the top priority in all seven themes and earn
  its points immediately by completing each item separately.
- Parents can optionally block new reward requests until all active assigned
  work is completed; existing reward requests and all other child actions
  remain available.
- New assigned work sends a theme-aware Web Push notification to the affected
  child's subscribed devices.

### Changed

- A catalog task is unavailable for assignment while it awaits approval, is
  already assigned, or has already been completed for that child today.

## [26.1.7] - 2026-07-30

### Fixed

- Family settings now use compact label, field, and helper-text rows matching
  the email and backup summaries, with properly reduced helper text and a
  responsive single-column mobile layout.

## [26.1.6] - 2026-07-30

### Changed

- Form labels, helper text, placeholders, section dividers, and field typography
  now use a clearer and more consistent visual hierarchy.
- Parent and child account creation actions use shorter wording.
- Email and backup summaries now separate muted labels from emphasized values
  in responsive definition lists.

### Fixed

- Reward approval actions now use the same approve and reject icons as task
  approvals.
- Child and parent activity history keeps point amounts aligned with status and
  photo controls on narrow screens.

## [26.1.5] - 2026-07-30

### Fixed

- The backup agent opens the live SQLite database with explicit `mode=ro` and
  `query_only`, while the data mount now permits SQLite to coordinate the
  locking and WAL files required for a safe online backup.
- Opening the source database and creating the local copy now produce distinct,
  actionable errors.

## [26.1.4] - 2026-07-30

### Fixed

- After a successful health check, the release updater now refreshes versioned
  `deploy` management scripts. This replaces stale server copies of
  `backup.sh` that still invoked the removed `restic` service.
- Updates continue to leave the local `deploy/.env`, family data, backups, and
  secrets untouched.

## [26.1.3] - 2026-07-30

### Changed

- The parent, landing, and shared system interface now uses the documented
  charcoal, muted gray, off-white, plum, sage, amber, and soft-red palette,
  with consistent field and helper typography.
- Email and backup configuration summaries use compact sentence-case lists,
  shorter settings actions, and consistently aligned buttons.
- The English and Lithuanian READMEs no longer use decorative icons or badges,
  include parent settings and two child-theme screenshots, and no longer link
  to the obsolete Orange Pi guide.

### Fixed

- An unconfigured backup now reports “Not enabled”, a running backup reports
  “Copying” in the main status indicator, and a healthy backup reports
  “Enabled” in green without a duplicate progress badge.
- PWA theme and background metadata now match the shared interface palette.

## [26.1.2] - 2026-07-30

### Fixed

- The backup agent now has a separate outbound Docker network for reaching S3
  while retaining its isolated internal connection to the application.
- Backup diagnostic commands now explicitly select `deploy/compose.yml`, so
  they work when run from the deployment root.

## [26.1.1] - 2026-07-30

### Changed

- The Settings page now uses one clear heading hierarchy, centered dividers,
  consistent field typography, styled select controls, primary action buttons,
  and matching green/red service status indicators.
- The project README now presents verified capabilities, privacy boundaries,
  deployment expectations, and screenshots made with fictional demo data.
- Backup documentation now distinguishes an invalid S3 hostname from Docker or
  host DNS failures and provides direct diagnostic commands.

### Fixed

- Sensitive settings ask for “Your account password” instead of the longer,
  account-type-specific wording.
- The activity-history filter no longer repeats a separate “Child” label next
  to the self-explanatory selector.
- Service-worker cache behavior is covered by a regression test that requires
  `Cache-Control: no-cache` on the worker script.

## [26.1.0] - 2026-07-30

### Added

- Parent administrators can verify and update SMTP settings from the Settings
  page; the SMTP password remains in a local permission-restricted secret file.
- The family name can now be edited from the general family settings.

### Changed

- Settings are organized into family, child and point, privacy, email, backup,
  account, and feedback sections.
- The seventh child theme is now the original Blockville theme with cube
  currency and trademark-neutral interface copy.

### Fixed

- Backup storage verification retries temporary Docker DNS failures and replaces
  low-level resolver output with an actionable endpoint message.
- Task, penalty, and reward edit forms consistently show colons after labels.

### Security

- Sensitive SMTP and backup credential changes require the current password of
  the parent administrator making the change. Account editing remains under its
  existing authentication rules.

## [26.0.0] - 2026-07-30

### Changed

- KinKudos is now a production release and no longer displays the BETA label.
- Version numbers now use `YY.FEATURE.FIX`: the year changes the first number,
  new functionality increments the second, and fixes, design work, or
  extensions of existing functionality increment the third.
- Feedback settings show unresolved reports by default and retain pagination;
  resolved reports remain available through the status filter.
- Backup settings distinguish an unconfigured orange state, a red stale or
  error state, and a green current state. Empty technical placeholders are
  replaced with concise human-readable values.
- Installation and upgrade documentation is repository-neutral, distinguishes
  KinKudos remote snapshots from whole-server backups, and recommends a
  dedicated restricted bucket for backup verification.

### Fixed

- Traefik is permanently instructed to reach the application through the
  external `web` network when the app also joins its internal backup network.
- The release updater assigns backup directories, agent credentials, and
  `restic` configuration to the configured application UID and GID even when
  the updater is run with `sudo`.
- Compose and updater regression tests protect the network selection and
  backup-file ownership fixes.
- The backup settings page no longer exposes
  `REPLACE_WITH_REPOSITORY`, and its destructive-change warning uses a
  softly red background.

## [0.13.0 BETA] - 2026-07-30

### Added

- Blockville World is a seventh child theme with a dark game-style interface,
  cube currency forms, challenge and prize wording, tactile controls,
  neon confetti, and its own completion sound in English and Lithuanian.
- Parent Settings now show backup provider, repository, last successful
  remote copy, integrity-check time, current activity, errors, and a
  seven-day health indicator.
- Parent administrators can verify Backblaze B2 or generic S3-compatible
  credentials and request an immediate encrypted backup from the web UI.
- A daily isolated backup agent copies the consistent SQLite database and
  private uploaded media, applies 31-day retention, and runs `restic check`.
- Dedicated English and Lithuanian Orange Pi ARM64 installation guides cover
  first-family setup, verification, backups, and upgrades.

### Changed

- The interactive installer now asks for language, hostname, allowed private
  networks, first-parent credentials, family name, and child profiles without
  embedding deployment-specific defaults.
- Existing provider-neutral `restic.env` and repository passwords are
  preserved and detected when upgrading from 0.12.4.
- The Lithuanian TODO now contains only outstanding device checks, restore
  tests, deferred providers, and newly identified work.

### Security

- Backup credentials are owned by an isolated container without a published
  port or Docker socket; the web application receives only sanitized status
  and never receives stored provider secrets.
- Backup configuration and manual requests are limited to the first parent
  administrator, require password confirmation for credential changes, and
  are audited without secret values.
- Family-specific names and a deployment-specific diagnostics username were
  removed from the current repository tree and demo/test data is generic.

## [0.12.4 BETA] - 2026-07-30

### Changed

- Child activity history now shows only the five most recent actions.
- Gift notifications use shorter wording and the recipient's themed point
  name without exposing the transferred amount in the notification text.
- Catalog create and edit forms consistently call the emoji field “Icon”.
- The project README now reflects the current BETA feature set, deployment
  model, supported platforms, and AI-project disclaimer.

### Fixed

- Language controls now show only the flag in a compact 44 px circular control,
  without the code or dropdown arrow that was misaligned on iPad.
- Notification controls now show only the bell in the same 44 px frame as the
  sign-out control, while keeping accessible state text.
- Release archives are built only from Git-tracked files, so ignored local
  caches and configuration cannot be included accidentally.

## [0.12.2 BETA] - 2026-07-29

### Added

- Task search now filters and suggests results from the first entered
  character, with keyboard Enter and touch selection support.
- Children can enable a daily random theme. Nightly maintenance changes it at
  most once per day.

### Fixed

- A rejected task appears in a clear parent-response card that the child can
  acknowledge, so stale responses no longer remain stuck on the page.
- Child history uses assigned task, reward, and gift icons, while push
  notifications use correct Lithuanian point and themed-currency forms.
- Theme and avatar controls share one appearance card, helper typography is
  consistent, and Lithuanian wording was corrected.
- Feedback screenshots open from a compact photo icon without displacing the
  status controls.
- The parent footer remains visible above mobile navigation and keeps
  consistent spacing from content on every parent page.

## [0.12.1 BETA] - 2026-07-29

### Added

- Children see approved balances, tasks, and reward decisions automatically:
  the page checks a small no-cache state endpoint while visible, refreshes on
  focus and push events, and waits while a dialog or edited form is open.
- A changed birthday now requires parent approval. The first birthday can be
  saved directly, only one change may wait at a time, and parent edits are
  retained as an approved audit record.
- Parent and child activity views identify the parent account that approved or
  rejected a task or reward request.

### Fixed

- Signed-in headers use the KinKudos logo, compact icon-only exit controls, and
  no longer repeat a family name or version. The project name and version are
  shown consistently in the footer.
- The settings card is now named “Project settings”.
- Feedback reports are collapsed by default and show a compact summary.
  Resolved reports use a green “Resolved” badge while open suggestions keep
  their violet type badge; filters and the current page remain selected after
  a status change.
- Birthday gifts remain limited to one award per child and calendar year even
  after an approved birthday change.

## [0.12.0 BETA] - 2026-07-29

### Added

- Children can instantly search the task catalog by name.
- Children can securely give already-earned points to another active child in
  the family. Both sides of the atomic transfer appear in activity history,
  and subscribed recipients receive a push notification.
- Children can save a birthday, while parents can configure an annual birthday
  point gift. The nightly maintenance job awards it once per calendar year,
  including February 29 birthdays on February 28 in non-leap years.
- Superhero HQ, Art Studio, and Panda World child themes add their own
  currencies, navigation language, task actions, colors, effects, and sounds
  in Lithuanian and English.

### Fixed

- Lithuanian empty-request and task-photo retention wording was corrected.
- Parent activity-history filtering and Previous/Next pagination remain on the
  History panel.
- Release validation now checks migration integrity before image build steps.
- Image builds remove stale Python bytecode before Django loads migrations, so
  cached modules cannot override a valid migration source file.
- Updates use one validated release archive and a separate version directory.
  Before switching containers, the server verifies its SHA256, builds the
  image, applies migrations to a clean temporary database, and backs up the
  production database.

## [0.11.1 BETA] - 2026-07-29

### Added

- A child who enables notifications on their device receives a targeted push
  when a parent approves or rejects their task, requests a correction, or
  approves or rejects a reward request. Parent comments and rejection reasons
  are included when available.

### Fixed

- Successful task and reward-request effects now work on iPhone and iPad:
  audio is unlocked by the child's tap, but it and the confetti play only
  after the server accepts the action. Errors and the following page load do
  not replay the effect.
- Pending task cards use a compact mobile layout with equal action targets and
  clear green, violet, and red decision semantics.
- The sound control consistently shows green for enabled and red for disabled
  in desktop browsers and on iOS.
- Lithuanian task revision and rejection dialogs no longer contain English
  explanatory text or field labels.

## [0.11.0 BETA] - 2026-07-29

### Added

- Signed-in parents and children can send a problem report or feature
  suggestion from an accessible floating bug button. Child wording is kept
  deliberately simple.
- Reports are saved in KinKudos before an optional email notification is sent.
  The report captures useful diagnostics without collecting passwords, PINs,
  cookies, session keys, or other form contents.
- Optional screenshots are validated, stripped of metadata, resized, converted
  to private WebP files, and protected by reporter/parent access checks.
- Parents can filter feedback, inspect its diagnostic context, open private
  screenshots, and move reports through New, Reviewed, Planned, and Resolved
  statuses in Settings.
- A provider-neutral `KINKUDOS_FEEDBACK_EMAIL` setting controls the notification
  recipient. Resolved-report screenshot retention is configurable and handled
  by the existing nightly maintenance job.
- Deployment includes a provider-neutral `configure-feedback.sh` helper that
  safely sets the feedback notification recipient in an existing `.env`
  without changing SMTP provider settings.

### Fixed

- Task approvals with photos now use compact, responsive cards that no longer
  break phone or desktop layouts. Evidence stays inside a cropped thumbnail
  and opens in the existing full-size viewer.
- Approve, request-revision, and reject actions use consistent icon buttons.
  Revision and rejection open focused dialogs with an optional comment which,
  when supplied, is visible to the child.
- Rejected tasks no longer disappear: parent activity history includes them at
  their decision time with a red stop status, optional comment, and access to
  retained evidence. Rejection does not create a point transaction.
- The parent photo viewer is wired to the same lightbox target as its
  JavaScript controller, so history camera icons and approval thumbnails once
  again open the retained full-size evidence.
- Parent activity history now includes rejected reward requests with a red stop
  status and the rejection reason. Approved reward requests carry a green
  confirmation status; both respect child filtering and pagination.
- The public changelog parser recognizes localized Lithuanian section headings,
  so the 0.10.3, 0.10.4, and later release notes are no longer displayed as
  empty.
- The child sound control now uses a stronger SVG speaker icon and the same
  44 px pill geometry as the neighboring toolbar controls.
## [0.10.4 BETA] - 2026-07-29

### Fixed

- Switching parent workspace sections in Safari keeps the page at the top
  instead of scrolling the selected panel underneath the sticky header.
  Versioned CSS, JavaScript, and app-shell cache URLs ensure browsers receive
  the fix.
- Home, tasks and rewards, and settings headings now start on the same
  alignment line. Parent navigation icons and labels also use consistent
  columns and axes.

## [0.10.3 BETA] - 2026-07-29

### Fixed

- Parent settings use the concise “Settings” heading.
- Public pages share the lightweight KinKudos product header while signed-in
  parent and child areas retain their family context.
- Pending requests and child cards use consistent vertical spacing on mobile,
  tablet, and desktop layouts.
- The language selector and notification control have the same exact height,
  and all four mobile navigation items use equal columns and visual centers.
- Active and disabled reward buttons retain identical dimensions in every
  child theme.

## [0.10.2 BETA] - 2026-07-29

### Fixed

- Reward request actions are enabled only when the child's current balance and
  configured credit can cover that reward. The server now rejects unaffordable
  requests even when the interface is bypassed.
- On iPhone, the pending-request panel sits closer to the child cards and all
  four bottom-navigation items use equal columns with centered content.
- The compact language selector now matches the notification control's pill
  shape and height while retaining a centered label and a 44 px target.
- The credit-limit information icon is vertically centered with its label.
- The public landing page uses a lightweight product header instead of the
  signed-in family toolbar; family context stays in the hero and the version
  link moves to the footer.
- The application icon now uses a readable amber-and-sage “KK” monogram on the
  KinKudos warm-plum background, with refreshed PWA, iOS, and notification
  sizes plus a matching browser favicon and versioned icon URLs.

## [0.10.1 BETA] - 2026-07-29

### Fixed

- Lithuanian pages no longer mix English headings, help text, buttons, or
  landing-page copy into the interface.
- Parent workspace headings use a simpler hierarchy without redundant eyebrow
  labels, and the settings sections have consistent vertical spacing.
- The language flag and code are geometrically centered in Safari and iOS,
  while the selector keeps a separate dropdown indicator and a 44 px target.
- Parent and landing interface colors were audited against the KinKudos brand
  palette, including accessible dark-mode and semantic state colors.

## [0.10.0 BETA] - 2026-07-29

### Added

- Optional task photo evidence from the camera or gallery, including HEIC/HEIF
  conversion to private WebP images, previews, configurable photo bonuses, and
  automatic retention cleanup.
- Parents can approve, reject, or return a submitted task for improvement; the
  child can replace the photo and submit it again.
- Child notifications, success confetti, theme-specific sound cues, and a local
  sound toggle.
- A mobile-first parent workspace with Home, Tasks and rewards, Settings, and
  History navigation. Pending decisions appear before child balances.
- 50% credit-use protection pauses new reward requests until the child's
  balance improves.

### Changed

- The generic currency is now Points. Block World uses emeralds and Magic
  Academy uses galleons, with correct English and Lithuanian number forms.
- Child theme navigation and actions now use their approved world-specific
  wording.
- Parent and landing interfaces use the KinKudos warm plum, sage, amber, cream,
  and charcoal palette.
- Block World uses square pixel-style cards and shadows; Magic Academy uses
  gold borders, seal-like actions, and warm glow interactions.

### Fixed

- Long child-card text and empty history text stay inside their containers.
- Child task cards keep readable text widths and full-width actions on iPad.
- Language flag and code are centered together.
- New suggestion icon fields start empty.

## [0.9.1 BETA] - 2026-07-29

### Fixed

- Negative token values are consistently red. Reward costs no longer use the
  positive-value green color.

## [0.9.0 BETA] - 2026-07-29

### Added

- Collapsible parent activity history with ten entries per page, localized
  pagination, and filtering by child.
- Country flags in the persistent English and Lithuanian language selector.
- Correct singular and plural token units in English and Lithuanian throughout
  balances, catalogs, requests, and activity history.

### Changed

- Task, penalty, and reward forms now consistently label their amount field
  “Tokens”. Penalties accept a positive amount and apply it as a deduction.
- Catalog and assignment token values now use consistent typography: tasks and
  rewards are green, while penalties are red.
- Every browser title follows “Page name – KinKudos”; the home title includes
  the family nickname.
- The family label in the top bar uses lowercase “family” or “šeima”.

### Fixed

- Zero and negative catalog amounts are rejected with a localized explanation.

## [0.8.5 BETA] - 2026-07-28

### Added

- Complete English and Lithuanian user interface with a persistent language
  selector.
- Browser language detection with English as the default for new installations.
- Bilingual first-run installation and generic family setup.
- Separate English and Lithuanian release notes.
- Mandatory theme selection when a child signs in for the first time.
- Required family name or nickname during initial setup, combined with the
  localized “Family” label throughout the interface.

### Changed

- The product is now named KinKudos. Family names remain separate,
  installation-specific data and are required during initial setup.
- New English installations use `Tokens` as the default currency name.
- Removed the former family-specific name from source code, file names,
  configuration variables, Docker resources, cookies, backups, and
  documentation. Internal identifiers now use the KinKudos name.
- The public repository documentation is now English-first.
- Child names use Lithuanian vocatives only while the Lithuanian interface is
  active.
- Existing child profiles remain ready to use after upgrading and are not
  forced through first-sign-in setup.

## [0.8.0 BETA] - 2026-07-28

### Added

- Parents can select and assign multiple completed tasks or penalties in one
  action.
- Assignment dialogs show checkbox lists with each item's icon and token value.

### Changed

- Batch assignments create separate history entries and run in one database
  transaction.

## [0.7.0 BETA] - 2026-07-28

### Added

- Secure parent password reset by a one-hour email link.
- Parent email address management and provider-neutral SMTP configuration.
- Public versioned changelog with “What's new?” and “What's fixed?” sections.
- The version number in the interface links to the changelog.

### Changed

- Password reset does not reveal whether an email address exists.
- SMTP credentials stay outside Docker images and Compose environment files.

## [0.6.0 BETA] - 2026-07-28

### Added

- Red delete buttons and confirmation prompts for task, penalty, and reward
  catalog entries.

### Changed

- Catalog deletion preserves earlier requests, balances, and activity history.
- New catalog item icon fields start empty.

## [0.5.0 BETA] - 2026-07-28

### Added

- Clear notification control with an SVG bell, status text, and iPhone setup
  guidance.
- `BETA` is shown next to every visible version label.

### Changed

- Balance colors, token label typography, credit limit wording, collapsed
  catalogs, and the Magic Academy owl action were corrected.

## [0.4.0] - 2026-07-28

### Added

- Parent and child account editing and safe deactivation.
- Four quick actions on every child card.
- iPhone HEIC/HEIF avatar conversion.
- Pending request count and dismissible status messages.

### Changed

- Catalog creation, account management, card typography, and penalty assignment
  layouts were reorganized and aligned.

## [0.3.0] - 2026-07-28

### Added

- Lithuanian child-name vocatives.
- Parent and child profile creation in the parent area.
- Web Push state management, penalty assignment, and credit dialogs.

### Changed

- Pending requests are grouped by child and ordered oldest first.
- Parent cards, terminology, and local SVG controls were refined.

## [0.2.0] - 2026-07-28

### Added

- Avatar upload and cropping, PIN changes, emoji selection, catalog editing,
  and visible application version diagnostics.

### Changed

- Balance colors, homepage copy, catalog controls, legacy icon conversion,
  Web Push error handling, Gunicorn startup, and migration failure handling.

## [0.1.0] - 2026-07-28

### Added

- Secure parent and child sessions with PIN lockout.
- Task, penalty, reward, suggestion, and savings-goal workflows.
- Immutable token ledger and configurable negative balance limit.
- Original Magic Academy and Block World themes.
- Installable PWA, offline page, Web Push, ARM64/AMD64 Docker, Traefik,
  SQLite backup, encrypted restic backup, and first-run management commands.
