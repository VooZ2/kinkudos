# KinKudos

<p align="center">
  <strong>A private, self-hosted family app for tasks, points, goals, and rewards.</strong><br>
  Turn everyday family tasks into visible progress. Children see what to do and work toward
  rewards, while parents review progress and keep the rules clear and fair. KinKudos runs on
  infrastructure you choose and administer, so you decide where your family data is stored.
</p>

<p align="center">
  <a href="https://demo.kinkudos.app/"><strong>🚀 Try the live demo</strong></a>
  ·
  <a href="https://docs.kinkudos.app/">📚 Documentation</a>
  ·
  <a href="https://kinkudos.app/">🌐 Visit the website</a>
  ·
  <a href="https://github.com/VooZ2/kinkudos/releases">📦 Latest release</a>
  ·
  <a href="README.lt.md">🇱🇹 Lietuviškai</a>
</p>

<p align="center">
  <a href="https://github.com/VooZ2/kinkudos/releases"><img src="https://img.shields.io/github/v/release/VooZ2/kinkudos?display_name=release" alt="Latest GitHub release"></a>
  <a href="https://hub.docker.com/r/vooz2/kinkudos"><img src="https://img.shields.io/docker/pulls/vooz2/kinkudos" alt="Docker pulls"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"></a>
</p>

## ✨ See it in action

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/parent-dashboard-2026.png" alt="KinKudos parent dashboard with pending family requests"></td>
    <td width="50%"><img src="docs/site/assets/parent-settings-2026.png" alt="KinKudos family settings and controls"></td>
  </tr>
  <tr>
    <td align="center"><sub><strong>Parent dashboard</strong><br>Review requests and make decisions in one place.</sub></td>
    <td align="center"><sub><strong>Family controls</strong><br>Manage rewards, privacy, devices, and family settings.</sub></td>
  </tr>
</table>

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/child-panda-dashboard-2026.png" alt="KinKudos Panda Pet child dashboard"></td>
    <td width="50%"><img src="docs/screenshots/child-block-world-dashboard-2026.png" alt="KinKudos Block World child dashboard"></td>
  </tr>
  <tr>
    <td align="center"><sub><strong>A world of their own</strong><br>Children can choose themes that make progress feel personal.</sub></td>
    <td align="center"><sub><strong>Tasks, rewards, and goals</strong><br>Everyday routines become clear missions and visible progress.</sub></td>
  </tr>
</table>

<p align="center">
  <img src="docs/screenshots/mobile-welcome-2026.png" width="31%" alt="KinKudos mobile welcome screen">
  <img src="docs/screenshots/mobile-parent-dashboard-2026.png" width="31%" alt="KinKudos mobile parent dashboard">
</p>
<p align="center"><sub>Add KinKudos to a supported phone, tablet, or computer as a Progressive Web App.</sub></p>

*Screenshots contain fictional demonstration data.*

## 🔄 How it works

1. 📝 A parent creates or assigns a task.
2. ✅ A child completes it and submits the result.
3. 👀 A parent reviews and approves the work.
4. 🎯 The child receives points and works toward a reward or savings goal.

## 💜 Why KinKudos?

### 👨‍👩‍👧‍👦 Clear for parents

Keep tasks, approvals, points, and rewards in one place while retaining control over family rules and final decisions.

### 🎮 Progress children can see

Children can view their tasks, collect themed points, request rewards, and save toward longer-term goals.

### 🔒 Private by design

One installation serves one household. There is no public registration, advertising, profiling, or built-in analytics inside the family app.

### 🏠 Yours to control

Run KinKudos on your own home server or VPS and decide where your family's data is stored.

## 🎯 What families can do

### 👨‍👩‍👧 Family workflow

- Tasks, daily assignments, and parent approvals
- Rewards, savings goals, point gifts, and birthday awards
- Child proposals and parent decisions
- Point corrections, penalties, and configurable credit
- A visible point history

### 🎨 Child experience

- Seven original visual themes with their own wording, sounds, and point units
- Child-friendly PIN sign-in from a paired browser or installed PWA
- Optional sounds and Web Push notifications
- Optional parent-controlled scratch tickets

### 🔐 Privacy and control

- One family per installation
- No public registration, advertising, profiling, or built-in analytics
- Uploaded task photos are resized, converted to WebP, and stripped of EXIF metadata
- Optional encrypted remote backups
- English and Lithuanian interfaces

## 🏡 Built for family life

KinKudos is not a workplace task manager adapted for children. It is designed around real family routines: simple tasks, parent approval, visible progress, themed points, rewards, and longer-term goals.

## ✅ Is KinKudos right for you?

### A good fit if

- you want one private space for one household;
- you already run a home server or VPS, or are willing to set one up;
- someone can maintain Docker, updates, HTTPS, and backups;
- you prefer control over a hosted subscription.

### Probably not a good fit if

- you want to register and start without any server setup;
- you need several unrelated families in one installation;
- you expect commercial support or a service-level agreement;
- you need location tracking, parental surveillance, or banking features.

Read [whether KinKudos fits your family](https://docs.kinkudos.app/start/is-kinkudos-right/) and explore the [KinKudos documentation](https://docs.kinkudos.app/) before installing.

## 🚀 Try the live demo

Explore the parent and child workflow without installing anything:

- **Demo:** [demo.kinkudos.app](https://demo.kinkudos.app/)
- **Parent username:** `demo`
- **Parent password:** `demo`
- **Child PIN:** `1234`

The public demo contains fictional data and resets every hour, so you can experiment freely.

## 🐳 Install KinKudos on your server

KinKudos runs on AMD64 and ARM64 Linux servers with Docker Engine and the Docker Compose plugin.

You will also need:

- a hostname or domain;
- HTTPS through a reverse proxy such as Caddy, Nginx, or Traefik;
- basic Linux and Docker administration skills.

For a fresh server that already has Docker Engine and Docker Compose:

```bash
curl -fsSL https://kinkudos.app/install.sh -o /tmp/kinkudos-install.sh \
  && sh /tmp/kinkudos-install.sh
```

The guided installer downloads the latest published KinKudos release, verifies its SHA256 checksum, creates the required application directories and configuration, and starts KinKudos with Docker Compose. The first family and parent administrator are then created securely in the browser; optional SMTP can be skipped and configured later. CLI administration remains available for recovery and advanced operations.

The command is for a **new installation**. Existing installations must use the documented update process.

### Manual Docker Compose setup

For a custom or already managed server, use the official release files in the
[`deploy/` directory](deploy/). Start from the configured `compose.yaml` in
that directory, not from an isolated Compose snippet:

```bash
docker compose up -d --pull always
```

Before running it, prepare the required environment variables and secret files,
persistent storage, a hostname or domain, HTTPS, and a correctly configured
reverse proxy. Keep the image pinned to a released version for predictable
deployments:

```yaml
image: vooz2/kinkudos:<version>
```

Using `latest` is an intentional choice to follow the newest stable image. After
the containers start, open the HTTPS hostname and complete the first-time setup
in the browser. The Compose deployment preserves its database and uploaded
media in persistent storage; back up those directories and secrets separately.

👉 **[Choose an installation method](https://docs.kinkudos.app/installation/)**

The documentation also covers HTTPS, updates, backups, recovery, diagnostics, and troubleshooting.

### ☁️ No home server?

A small Docker-capable VPS is usually one of the simpler ways to run KinKudos privately on the internet. KinKudos works with any suitable VPS provider. Hostinger VPS is one available option for users who prefer a guided commercial service.

<p>
  <a href="https://www.hostinger.com/vps/docker-hosting?compose_url=https://raw.githubusercontent.com/VooZ2/kinkudos/main/deploy/hostinger/compose.yaml&REFERRALCODE=LKIGEDIMICSU#pricing">
    <img src="https://img.shields.io/badge/Hostinger_Docker_VPS-Deploy_on_Hostinger-673DE6?logo=hostinger&logoColor=white" alt="Deploy on Hostinger">
  </a>
</p>

> **Referral offer:** The link may provide a discount or other benefit on eligible Hostinger services, depending on the current offer. I may also receive a commission at no additional cost to you. Hostinger is optional and is not an official KinKudos partner.

The link opens Hostinger’s Docker VPS selection and passes the KinKudos Compose URL to Docker Manager. After choosing a VPS, provide your hostname and private setup token; finish the first family setup in the browser. Follow the [Hostinger VPS step-by-step guide](https://docs.kinkudos.app/installation/hostinger/). Hostinger is a paid external service; KinKudos remains free and self-hosted.

## ⚙️ Architecture

- Django 5.2
- Server-rendered HTML
- Vanilla JavaScript PWA
- SQLite in WAL mode
- Gunicorn
- WhiteNoise
- Docker
- Web Push with VAPID

No Node.js runtime, SPA framework, or public API is required for normal operation.

## 💡 Why I built KinKudos

I wanted a simple and private way to manage family tasks, points, and rewards without relying on a hosted service.

I am not a professional software developer. KinKudos also began as a practical experiment: could I use OpenAI Codex to turn a real family problem into a maintainable, tested, and documented open-source application?

The project grew from that experiment into software used in a real household and published for other families who may find it useful.

OpenAI Codex has assisted extensively with implementation, refactoring, tests, documentation, and release preparation. Product direction, requirements, review, validation, infrastructure, releases, and ongoing maintenance remain my responsibility.

## 🛡️ Security and privacy

KinKudos is designed as a private space for one household.

- Parent accounts use rate-limited password authentication.
- Children use a paired browser or installed PWA together with a rate-limited PIN.
- Point changes are transactional and added to a visible point history.
- Task photos, database files, backups, and credentials stay outside the public source repository.
- Optional encrypted remote backups support Backblaze B2 and S3-compatible storage.
- KinKudos contains no advertising, profiling, or built-in analytics inside the family app.
- Family data is not sent to a KinKudos-operated cloud service.

Self-hosting gives you control, but it also makes you responsible for HTTPS, server security, updates, and tested backups.

Read [SECURITY.md](SECURITY.md) for vulnerability reporting and security support information. Additional privacy and server-security guidance is available in the [KinKudos documentation](https://docs.kinkudos.app/).

Report unpatched security vulnerabilities privately, never in a public GitHub issue.

## 📚 Documentation

The complete documentation is available at **[docs.kinkudos.app](https://docs.kinkudos.app/)**.

Useful starting points:

- [What is KinKudos?](https://docs.kinkudos.app/start/what-is-kinkudos/)
- [Is KinKudos right for my family?](https://docs.kinkudos.app/start/is-kinkudos-right/)
- [Your first 15 minutes](https://docs.kinkudos.app/start/first-15-minutes/)
- [Choose an installation method](https://docs.kinkudos.app/installation/)
- [Install on a Hostinger VPS](https://docs.kinkudos.app/installation/hostinger/)
- [Guided server installer](https://docs.kinkudos.app/installation/guided-installer/)
- [Docker Compose installation](https://docs.kinkudos.app/installation/docker-compose/)
- [First-time web setup](https://docs.kinkudos.app/installation/first-time-setup/)
- [Updating and backups](https://docs.kinkudos.app/installation/updating/)
- [Troubleshooting and CLI administration](https://docs.kinkudos.app/troubleshooting/)

## 📌 Project status and support

KinKudos is actively maintained and used in a real household.

Support is provided on a best-effort basis, without a service-level agreement or guaranteed response time. Only the latest published release is supported. Users should review release notes and maintain tested backups before updating.

- [Latest releases](https://github.com/VooZ2/kinkudos/releases)
- [Release notes](CHANGELOG.md)
- [KinKudos documentation](https://docs.kinkudos.app/)

## 🧑‍💻 Local development

KinKudos requires Python 3.12. After creating a virtual environment and installing the dependencies from `requirements.txt`:

```bash
python scripts/compile_translations.py
python manage.py migrate
python manage.py test economy.tests
python manage.py runserver
```

The `seed_demo` command is development-only and refuses to modify a non-empty database.

Before changing authentication, permissions, point accounting, backup behaviour, or deployment logic, read the repository documentation and existing tests.

## 🤝 Contributing and feedback

Bug reports, documentation corrections, translations, and focused pull requests are welcome. For larger changes, open an issue first to discuss the use case and scope.

- [Search or open GitHub issues](https://github.com/VooZ2/kinkudos/issues)
- [Read the release notes](CHANGELOG.md)
- [Report security issues privately](SECURITY.md)

The in-app feedback form sends feedback to the administrator of that KinKudos installation. It does not contact the KinKudos project maintainer.

Do not publish passwords, secret keys, private family photos, database files, backup files, personal information, or unredacted logs in GitHub issues.

## ☕ Support KinKudos

KinKudos is free and open source. If it is useful to your family, you can support its continued maintenance with a one-time coffee.

Support helps cover the domain, public demo, documentation, testing, and other project infrastructure. It does not provide priority support, guaranteed features, faster issue resolution, or influence over security decisions.

<p>
  <a href="https://buymeacoffee.com/vooz2">
    <img src="https://img.shields.io/badge/Buy_Me_a_Coffee-Support_KinKudos-FFDD00?logo=buymeacoffee&logoColor=000000" alt="Support KinKudos on Buy Me a Coffee">
  </a>
</p>

## 📄 License

KinKudos is open-source software distributed under the [MIT License](LICENSE).

The software is provided as-is, without warranty of any kind.
