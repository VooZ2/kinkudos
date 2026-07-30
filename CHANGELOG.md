# Changelog

All notable project changes are documented in this file. The format follows
Keep a Changelog and the versions follow Semantic Versioning.

## [Unreleased]

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
