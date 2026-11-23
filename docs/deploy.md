# Running Trove live

This is the manual for the live site: what it is made of, who owns each account, how to change anything, and
what to do when something breaks. It is written so that anyone on the team can run the site without asking the
person who set it up. It is plan item G1.

**Where things stand:** the site runs on free tiers, so it is a demo, not a production service. See
[Free-tier limits](#free-tier-limits-what-to-expect) before inviting real people.

Nothing secret is written in this file, and nothing secret may ever be added to it. This repository is public.
Secrets live in the host's dashboard and in the team's password manager (see
[Secrets](#secrets-and-who-holds-them)).

## Start here (teammates)

**Where it stands.** The site is deployed on Render and Daniel has shared its address with you. It is a work in
progress: it may be broken in places, and you can fix it. Nobody has proven yet that a verification code arrives
in a real inbox. Daniel added the Brevo API key (`BREVO_API_KEY`) to Render, and the email path through it was
tested only with the network faked.

**What you can do without any account.**
- Open the site and `<address>/api/health`. It must answer `{"ok":true,"database":true}`. If the page says
  "Service Suspended", or never loads, the problem is on Render's side and only the Render owner can see it.
- Try the app as a member and note what breaks. Real members sign up with a case.edu email (a code is sent) or
  with an invite link from a member (Settings → Invite an alum).
- Reproduce a problem on your own machine: `python3 scripts/dev.py` (see the README), which prints email codes in
  the terminal. Most bugs are the app's, not the host's.
- Fix code and ship it. Render watches the branch **`daniel/g1-go-live`**, so a fix pushed to that branch goes
  live on its own in about 5 to 10 minutes (a build that fails leaves the old version running). Make the fix on
  your own branch off it, run `python3 scripts/check.py`, then push to `daniel/g1-go-live` (or, if you prefer,
  merge the pull request first and ask the owner to point Render at `main`). Tell the others in the chat first,
  so two people don't push at once.

**What needs the Render owner (Daniel).** Reading Render's Logs, changing settings or keys (the Environment
page), restarting or redeploying, and pointing Render at another branch. The free plan allows no other member
([why](#sharing-render-with-the-team)). If you need a log line, ask Daniel to paste it, with no secrets in it.

**Never** put a secret in the chat, a pull request, an issue or a file in the repository (it is public). Rotate it
if you did ([how](#rotate-a-secret)).

**Where to look when something breaks:** [When something breaks](#when-something-breaks) lists every problem we
have already met and its fix, with the exact log line to look for. [Every setting](#every-setting-and-where-it-comes-from)
says what each environment value is for.

## Contents

1. [How it is put together](#how-it-is-put-together)
2. [Accounts and who owns them](#accounts-and-who-owns-them)
3. [Every setting, and where it comes from](#every-setting-and-where-it-comes-from)
4. [Day to day: shipping a change](#day-to-day-shipping-a-change)
5. [When something breaks](#when-something-breaks)
6. [Routine jobs](#routine-jobs)
7. [Setting it all up from nothing](#setting-it-all-up-from-nothing)
8. [A real domain](#a-real-domain)
9. [Secrets and who holds them](#secrets-and-who-holds-them)
10. [Free-tier limits: what to expect](#free-tier-limits-what-to-expect)
11. [What has and hasn't been checked](#what-has-and-hasnt-been-checked)
12. [Before you invite real members](#before-you-invite-real-members)

## How it is put together

```
 member's browser
        |   https://<the service address>
        v
  Render  (one free "web service", built from the Dockerfile)
   |-- /api/...   the FastAPI app (api/trove/main.py)
   '-- everything else: the built React website (web/dist), served by api/trove/serve.py
        |                         |                        |
        v                         v                        v
  MongoDB Atlas            Anthropic API             Brevo (email, over HTTPS)
  (database trove_prod)    (the Librarian,           (verification codes,
                            the interview)            reminders, notices)
```

- **One service.** The API answers under `/api` and also serves the website, so the browser talks to one address.
  There is no separate website host, no proxy and no cross-site settings. The website's own `/api/...` calls
  work exactly as they do in development (`api/trove/serve.py`, tested in `api/tests/test_serve.py`).
- **The image** is built from the `Dockerfile` at the repository root: stage one builds the website with Node,
  stage two installs the API with `uv` and copies the built website in. Render builds it itself; nobody builds
  images by hand.
- **`render.yaml`** (a Render "Blueprint") describes the service: free plan, Virginia region, health check at
  `/api/health`, and the list of settings. It contains no secrets.
- **Email goes out through Brevo's web API** (plain HTTPS), not SMTP, because Render's free tier blocks the
  SMTP ports. This is `BREVO_API_KEY` (see the settings table).
- **Attempt limits** (sign-up, sign-in, codes) are counted per caller address. Behind Render's proxy the app
  reads the real address from the end of `X-Forwarded-For`, because of `TRUSTED_PROXY_HOPS=1`.

## Accounts and who owns them

Whoever created an account is its owner, and the others have no access unless they are added. **Add the others
now where the plan allows, so the site never depends on one person.** The login details for the shared accounts (Gmail, Brevo) belong
in the team's password manager (Bitwarden or 1Password), not in chat or in the repository.

| Service | What it does for Trove | Owner today | How to add a teammate | Free-tier limits |
|---|---|---|---|---|
| **Render** (render.com) | Hosts the site | Daniel (signed in with GitHub) | **Not possible on the free plan:** a free (Hobby) workspace allows one member only ([Render's docs](https://render.com/docs/team-members)). Members can be invited (Workspace Settings → Team members → Invite) only on a paid Pro workspace. See [Sharing Render](#sharing-render-with-the-team). | 750 instance hours a month (enough for one always-on service); sleeps after 15 minutes idle |
| **MongoDB Atlas** (cloud.mongodb.com) | The live database | Daniel, in his own organization; project **Trove**, cluster **trove** | Project → **Access Manager → Invite to project**, as *Project Owner* | Free "M0": 512 MB storage |
| **Brevo** (brevo.com) | Sends email | A shared Gmail account made for Trove | The free plan may allow only one user, so share the login through the password manager | 300 emails a day |
| **Anthropic** (console.anthropic.com) | The AI | Josef (the team's shared key) | Ask Josef | Pay as you go: costs real money |
| **GitHub** | The code and the deploy trigger | Daniel owns the repo (`r6vie/senior_capstone`) | Already shared with the team | Free |

The Gmail account made for Trove is the *login* for Brevo and the *sender address* on every email. Whoever holds
its password can recover Brevo, so it must be in the password manager too.

**Names to find things by (not secrets):** the Atlas project is called **Trove**, its cluster **trove**, its
production database **`trove_prod`**, and its database user **`trove_prod_app`** (it can only read and write
`trove_prod`). The Render service is called **trove**.

## Every setting, and where it comes from

The service reads these from its environment (Render → the service → **Environment**). The same names work in a
local `.env`, which is how the code reads them (`api/trove/core/config.py`). `.env.example` lists the local ones.

Two kinds of setting exist, and they are changed in different places:

- **Fixed in `render.yaml`** (the "value" column is filled in): change them by editing `render.yaml` and merging
  it. Render re-applies the file and may **overwrite a change made in the dashboard**.
- **Secret or per-person** (marked *dashboard*): change them only in Render's Environment page. They are not in
  the repository. After saving, Render redeploys by itself.

| Setting | Value / where it comes from | Where to change |
|---|---|---|
| `ENVIRONMENT` | `production` (also stops the canned "scripted AI" from ever running live) | `render.yaml` |
| `MONGODB_DATABASE` | `trove_prod` | `render.yaml` |
| `MONGODB_URI` | The Atlas connection string for user `trove_prod_app`, with its password in it. Atlas → Database → **Connect** → **Drivers**. **Secret.** | dashboard |
| `ANTHROPIC_API_KEY` | The team's Anthropic key. **Secret.** | dashboard |
| `AI_BUDGET_USD` | A safety net, such as `20`. The ledger is a file that Render wipes on each restart, so it is *not* the real spending cap (see [AI spending](#ai-spending)). | dashboard |
| `BREVO_API_KEY` | Brevo → account menu → **SMTP & API → API Keys**. An *API* key, not an SMTP key. **Secret.** | dashboard |
| `EMAIL_FROM` | `Trove <address>`, where the address is a sender verified in Brevo (Brevo → Senders). | dashboard |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | Only used if `BREVO_API_KEY` is empty. On Render's free tier, SMTP is blocked, so these are left unused. | dashboard / `render.yaml` |
| `EMAIL_LINK_SECRET` | Generated once by Render (`generateValue`). It signs the unsubscribe links in emails. **Never change it without a reason**: changing it breaks every unsubscribe link already sent. | Render generates it |
| `FRONTEND_URL` | The site's address, such as `https://trove.onrender.com` (no slash at the end). Used in links inside emails and in invite links. | dashboard |
| `API_URL` | The same address with `/api` on the end. Used in the unsubscribe link. | dashboard |
| `TRUSTED_PROXY_HOPS` | `1` (Render's load balancer is one proxy). See [Too many attempts](#everyone-gets-too-many-attempts). | `render.yaml` |
| `VERIFICATION_REQUIRED` | Unset, which means **on**: a case.edu code or an invite is needed to sign up. Never turn it off live. | not set |
| `PORT` | Set by Render. | automatic |

## Day to day: shipping a change

**The normal route.** Render watches one branch and redeploys whenever it changes.

1. A change is made on a branch and a pull request is merged into `main` (the usual rules in
   [CONTRIBUTING.md](../CONTRIBUTING.md): CI must pass first).
2. Render sees the new commit on the branch it watches and starts a build (about 5 to 10 minutes).
3. When the build finishes, the service switches to the new version. If the build fails, the old version keeps
   running, so a broken build does not take the site down.
4. Check it: open `https://<address>/api/health`. It must answer `{"ok":true,"database":true}`.

**Which branch does Render watch?** During setup it was pointed at the branch `daniel/g1-go-live`. **After that
branch is merged into `main`, change it to `main`** (Render → the service → **Settings → Build & Deploy →
Branch**). If the branch is deleted by a merge and Render still watches it, deploys stop silently.

**Watching a deploy.** Render → the service → **Events** shows each deploy and whether it succeeded;
**Logs** shows the build and then the running app.

**Rolling back.** Render → the service → **Events** → find the last good deploy → **Rollback**. Then fix the
problem on a branch and merge again. (Rolling back does not change the database.)

**Restarting.** **Manual Deploy → Clear build cache & deploy** rebuilds from scratch, and **Restart** just
restarts. Restarting wipes the service's disk, which is fine: nothing important is stored there.

**Changing a database model or collection.** There are no migrations. The app creates its own indexes when it
starts. Anything that changes how existing documents look has to handle the old shape, because the live
database keeps its data between releases.

## When something breaks

Start with these two, which settle most problems:

1. `https://<address>/api/health`
   - Doesn't load at all: the service is asleep (wait up to a minute and reload), stopped, or the build failed.
     Check Render → **Events**.
   - `{"ok":true,"database":false}`: the app is up but can't reach the database. See [The database](#the-database-is-not-connected).
   - `{"ok":true,"database":true}`: the app and database are fine. The problem is elsewhere.
2. Render → **Logs**. Errors are written there. Search for `failed`, `Error` and `Traceback`.

### The site takes about a minute to open

The free service sleeps after 15 minutes without traffic. The first visit wakes it. Nothing is wrong. To avoid
this you need a paid instance (about $7 a month), or a keep-alive ping, which Render discourages.

### The database is not connected

`/api/health` says `"database":false`, or sign-up errors.
1. Look in **Logs** for a line about authentication or timeout when the service started.
2. **Authentication failed:** the password in `MONGODB_URI` is wrong or has a special character. In Atlas →
   **Database Access** → edit `trove_prod_app` → **Edit Password** (letters and numbers only), update
   `MONGODB_URI` in Render, and keep the new password in the password manager.
3. **Timeout:** in Atlas → **Network Access** there must be an entry for `0.0.0.0/0` with status Active.
4. **Check the string by itself**, from a developer's machine, without printing it:
   `cd api && python -m uv run python ../scripts/check_atlas.py` (it asks for the string with hidden input and
   should print three `PASS` lines).
5. Atlas free clusters pause after about 60 days with no activity. Atlas → **Database** → **Resume** if it shows paused.

### Verification codes or other emails don't arrive

1. Render → **Logs** → search `Email to user`. The line says why it failed, after the colon:
   - `HTTPError 401` / `Key not found`: `BREVO_API_KEY` is wrong, or it is an SMTP key. Make a new **API** key in
     Brevo (SMTP & API → API Keys) and update it in Render.
   - `HTTPError 400` mentioning the sender: `EMAIL_FROM` is not a verified sender. In Brevo → **Senders**,
     verify it, or change `EMAIL_FROM` to one that is.
   - `HTTPError 403` or a message about IP addresses: in Brevo, SMTP & API, switch off the option (if it is on)
     that blocks unknown IP addresses for API keys. Render's free tier has no fixed address.
   - `TimeoutError` or `OSError`: mail is going out by SMTP, which is blocked. `BREVO_API_KEY` must be set.
   - A line beginning `[email not configured]`: neither `BREVO_API_KEY` nor `SMTP_HOST` is set. The email text,
     including the code, is printed in that log line, so a developer can still read a code from there.
2. **No `failed` line:** the email left the server. Check Brevo → **Transactional → Logs** to see what happened
   to it (delivered, blocked, deferred).
3. **Delivered but not in the inbox:** look in spam and, for a case.edu address, in the school's quarantine.
   Brevo warns that a `gmail.com` sender can't be authenticated, so Google-hosted inboxes (case.edu is one) may
   hide these emails. The fix is a sender on a domain the team owns: see [A real domain](#a-real-domain).
4. **A student can ask again** from the verify page ("Send me a new code"), at most once a minute.
5. Brevo sends 300 emails a day on the free plan. Brevo → **Transactional → Logs** shows how many went out.

### Everyone gets "Too many attempts"

Sign-up, sign-in and code checks are limited per caller address. If everyone is blocked together, the app is
seeing the same address for everybody, so `TRUSTED_PROXY_HOPS` is wrong. It should be `1` on Render. To test:
1. Enter a wrong password 11 times from one browser. The 11th must say "Too many attempts".
2. Open the site on a phone using mobile data and sign in. It must work.
If the second step is also blocked, try `2` (another proxy sits in front). If the first step never blocks, set
`0` and tell a developer. Both are changes in `render.yaml`.

### The AI doesn't answer

1. **Logs** → search `Anthropic`, `BudgetExceeded` and `401`.
2. `BudgetExceeded`: the in-app `AI_BUDGET_USD` was reached. It resets on the next restart (the ledger is wiped),
   but check actual spending in the Anthropic console first, so you know it isn't a runaway.
3. `401` / authentication: `ANTHROPIC_API_KEY` is wrong or has been revoked. Ask Josef.
4. The console's own spend limit may have been hit. Check it in the Anthropic console.

### A build fails

1. Render → **Events** → the failed deploy → **Logs**, scroll to the first red line.
2. If the **website** step fails (`npm`), run `npm --prefix web run build` locally to see the same error.
3. If the **API** step fails (`uv sync`), run `cd api && python -m uv sync --frozen --no-dev` locally.
4. The old version keeps serving while a build fails.

### A page loads but shows old content

Pages are never cached, but the built files are named by their content. If someone sees an old version, a hard
refresh (Ctrl+Shift+R) fixes it, and the deploy may simply not be finished: check Render → **Events**.

## Routine jobs

### Add a teammate to the accounts

See the table in [Accounts and who owns them](#accounts-and-who-owns-them). Atlas can invite people for free;
Render cannot (below). Each person should open the logins they have once, to know they work.

### Sharing Render with the team

A free Render workspace has one member, so teammates cannot be added. Do not share the owner's login: it is
tied to that person's GitHub account. The options are:

1. **Upgrade to a Pro workspace** (paid; check the current price on Render's pricing page, since its pages
   disagree on whether it is per member or flat) and invite everyone.
2. **Each teammate runs their own copy** on their own free Render account, from `render.yaml` and the steps in
   [Setting it all up from nothing](#setting-it-all-up-from-nothing). That is a separate site with its own
   address, not access to this one. The secrets are handed over through the password manager.
3. **The owner stays the only Render user.** Everyone else fixes problems by pushing a change to the branch
   Render watches (it redeploys by itself), and anything that needs a setting, a log or a restart goes through
   the owner. This is cheapest but depends on the owner being reachable.

Without Render access, a teammate can still: change the code (by pushing to the watched branch), read the
public site and `/api/health`, and check Brevo and Atlas if they have those logins. They cannot read Render's
Logs, change its settings or keys, or restart it.

### AI spending

The real spending cap is a **monthly limit in the Anthropic console** (Settings → Limits), set by whoever owns
the account (Josef). `AI_BUDGET_USD` is only a backstop, because its ledger is a file that Render erases on each
restart. Look at actual use in the console now and then, especially after inviting people. If the key is
revoked, every teammate's local `.env` stops working too, which is why a key made just for the live site is
better. When one exists, replace `ANTHROPIC_API_KEY` in Render only.

### Rotate a secret

Do this whenever someone leaves, a secret might have been seen, or before launch to real members.

| Secret | How |
|---|---|
| Atlas password | Atlas → **Database Access** → edit `trove_prod_app` → **Edit Password**. Put the new connection string into `MONGODB_URI` in Render. Run `check_atlas.py` first. |
| Brevo API key | Brevo → **SMTP & API → API Keys**: make a new one, put it in `BREVO_API_KEY`, then delete the old one. |
| Anthropic key | Ask Josef for a new key. Replace `ANTHROPIC_API_KEY` in Render. |
| Gmail / Brevo login | Change the password; update the password manager. |

Never paste a secret into chat, a pull request, an issue or a file in the repository. If one was pasted anywhere,
treat it as leaked and rotate it.

### Check what is in the database

Atlas → **Database** → **Browse Collections** → `trove_prod` shows members, books, checkouts and messages.
That is private data about real people: look only to debug, and don't copy it anywhere.

### Delete or reset the live data

Deleting an account from Settings removes the member's data everywhere (books, checkouts, meetings, messages,
invites). To empty the whole database (for example after a demo), Atlas → Browse Collections → drop each
collection in `trove_prod`. The app makes its indexes again when it starts. There is no undo.

### The Brevo SMTP key

Brevo SMTP keys expire after a year, and after 90 days without use. API keys may behave the same way (check the
expiry shown when you make one). If email stops after a quiet spell, make a new key (see Rotate a secret). The older SMTP key made during setup is not used and
can be deleted in Brevo.

## Setting it all up from nothing

Only needed to rebuild the live site, for example under a new account. Do these in order.

### 1. The database (Atlas)

1. Sign in at https://cloud.mongodb.com with the account that will own it (not a teammate's organization: don't
   touch the dev cluster the team shares).
2. Make a project named `Trove`, then a free cluster: the **M0 Free** tier, provider AWS, region N. Virginia, named
   `trove`. Decline any upgrade or "Automate security setup" offers.
3. **Security → Database Access → Add New Database User:** username `trove_prod_app`, a long random password
   (letters and numbers only: symbols such as `@ : / ? # %` break the connection string). Under **Specific
   Privileges** give it `readWrite` on the database `trove_prod` and nothing else.
4. **Security → Network Access → Add IP Address:** `0.0.0.0/0` ("Allow Access From Anywhere"). Render's free tier
   has no fixed address, so this is needed. The password and the user's limit to `trove_prod` are what protect
   the data.
5. **Database → Connect → Drivers:** copy the string and replace `<db_password>` with the real password.
6. Test it from a checkout of the repository, in your own terminal:
   `cd api && python -m uv run python ../scripts/check_atlas.py`. Paste the string when asked (hidden). It must
   print the host of *your* cluster and three `PASS` lines.

### 2. Email (Brevo)

1. Make a Gmail account just for Trove (not a personal one) and put its login in the password manager.
2. Sign up at https://www.brevo.com with it. Free plan only; never add a card.
3. **Senders, Domains & Dedicated IPs → Senders:** the Gmail address should be listed as verified. If not, add
   it and click the verification link Brevo emails to that address.
4. **SMTP & API → API Keys → Generate a new API key**, named `render`. Copy it immediately (it is shown once)
   into the password manager. Leave "block unknown IP addresses" off.
5. Not needed on Render's free tier: SMTP keys. They are blocked by the host.

### 3. The host (Render)

1. Sign in at https://render.com with GitHub, with the account that owns the repository or has access to it.
   If asked, install the Render GitHub app for `r6vie/senior_capstone`.
2. **New + → Blueprint**, pick the repository, and pick the branch (use `main`, once this work is merged).
3. Render reads `render.yaml` and shows the `trove` service on the free plan in Virginia. If it asks for a card,
   stop and discuss it as a team first.
4. Fill in the values it asks for (the *dashboard* ones in the settings table above):
   `MONGODB_URI`, `ANTHROPIC_API_KEY`, `AI_BUDGET_USD` (such as `20`), `BREVO_API_KEY`, `EMAIL_FROM`
   (`Trove <the verified sender>`), and for now `FRONTEND_URL` `https://trove.onrender.com` and `API_URL`
   `https://trove.onrender.com/api`. Leave the SMTP values empty.
5. **Apply.** The first build takes 5 to 10 minutes.
6. When it is **Live**, the service page shows its address at the top. If it is not exactly
   `https://trove.onrender.com`, set `FRONTEND_URL` to it and `API_URL` to it plus `/api` (Environment tab) and
   let it redeploy.
7. Decide how the team will share it (see [Sharing Render](#sharing-render-with-the-team)).

### 4. Prove it works

1. `https://<address>/api/health` must show `{"ok":true,"database":true}`.
2. Open the address and see the landing page.
3. Sign up with a real case.edu address. A code must arrive (check spam), and entering it must sign you in.
4. Start the book interview and answer one question, to prove the AI key works.
5. The attempt-limit test under [Everyone gets "Too many attempts"](#everyone-gets-too-many-attempts).
6. In Settings, make an invite link, open it in a private window, and sign up as an alum without a case.edu
   address.

## A real domain

The free address from Render (`...onrender.com`) is fine to start. For a proper one, claim a free `.me` (or one of
the other extensions) from the GitHub Student Developer Pack, through the pack's Namecheap or Name.com offer. It
is free for a year and renews at the normal price after. Check the live offer before relying on it. The
domain is registered in one person's name, so agree who holds it and write it down.

1. Render → the service → **Settings → Custom Domains → Add**, and add the domain.
2. Render shows the DNS records to add. Add them at the registrar.
3. When Render shows the domain as verified, change `FRONTEND_URL` and `API_URL` to the new address.
   Links in emails sent earlier still point at the old address, so do this before sending many.
4. **Fix email at the same time.** In Brevo → **Senders, Domains & Dedicated IPs → Domains**, add the domain,
   and add the DNS records Brevo shows (they sign the emails so they stop landing in spam). Then use an address
   on that domain as the verified sender and in `EMAIL_FROM`.

## Secrets and who holds them

- **Where they live:** only in Render's Environment page and the team's password manager. Never in the
  repository (it is public), in chat, in a screenshot or in a pull request. `.env` files are ignored by git
  and are never baked into the image (`.dockerignore`).
- **Who can read them:** anyone on the Render team and the Atlas project. Add only people who need access.
- **What a leaked one allows:**
  - `MONGODB_URI`: read and change all live data. Rotate immediately.
  - `ANTHROPIC_API_KEY`: spend the team's money. Revoke it and get a new one.
  - `BREVO_API_KEY`: send email as Trove. Delete it and make a new one.
- **The database is open to the internet** (`0.0.0.0/0`), protected only by the password and a user that can
  touch nothing but `trove_prod`. Use a long random password, and don't reuse it anywhere.
- **Live data is separate from development data.** The live database is `trove_prod` on its own cluster. Local
  `.env` files point at the team's shared dev cluster. Don't mix them up: never point a local run at the live
  string.

## Free-tier limits: what to expect

| Limit | What happens | What it means |
|---|---|---|
| Render sleeps after 15 min idle | The first visit takes up to ~a minute | Fine for a demo; bad for a first impression. A paid instance (about $7 a month) removes it. |
| Render's disk is wiped on restart | Nothing important is stored on disk, except the AI ledger | `AI_BUDGET_USD` resets on every restart: use the Anthropic console limit |
| Render 750 hours a month | About one always-on service fits | Don't add a second service in the same workspace |
| Atlas free: 512 MB | Writes fail when it is full | Plenty for a demo; watch it in Atlas → Database |
| Brevo free: 300 emails a day | Further emails are refused until the next day | A busy launch day could run into it |
| Brevo and a gmail.com sender | Emails to Google-hosted inboxes may be hidden | Needs a domain the team owns (see A real domain) |
| Anthropic | Costs money | The monthly limit in the console is the only real cap |

## What has and hasn't been checked

**Checked**
- The combined server (`trove.serve`), its caching rules and its refusal to read files outside the website:
  `api/tests/test_serve.py`.
- The proxy-aware attempt limits: `api/tests/test_client_address.py`.
- Sending mail through Brevo's web API, including failures and retries (with the network faked, so no real
  email in tests): `api/tests/test_brevo_send.py`.
- The `Dockerfile` and `render.yaml` built and ran on Render: the site came up and served.
- The Atlas cluster accepts connections, writes and indexes: `scripts/check_atlas.py`.

**Not yet checked** (do these first, and tick them off in the pull request or here)
- A real verification code arriving through Brevo's API at a real case.edu inbox. Mail was shown to fail by
  SMTP on Render, and the API route was added afterwards but not yet tried live.
- The attempt-limit test under `TRUSTED_PROXY_HOPS=1`.
- The AI working through the live site on the team's key, and what a day of use costs.
- Where a gmail.com sender's mail ends up for case.edu recipients.

## Before you invite real members

- [ ] A verification code arrives at a real case.edu address (check spam), and works.
- [ ] The attempt-limit test passes (two steps above).
- [ ] The AI interview works live.
- [ ] A monthly spend limit is set in the Anthropic console, and Josef agrees to use the team key (or has made a
      separate one).
- [ ] Teammates have what they need: the Atlas project (invite them), the Brevo login, and a plan for Render (see Sharing Render).
- [ ] Render watches `main`, not a feature branch.
- [ ] Passwords for Atlas, the Trove Gmail account and Brevo are in the password manager.
- [ ] A decision has been made on a real domain and on fixing email deliverability.
- [ ] Someone has read the privacy-sensitive parts of the app once on the live site: contact details only appear
      after an accepted checkout, and deleting an account removes everything.
