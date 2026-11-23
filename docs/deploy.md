# Going live

How Trove runs on a free host, and what each person has to supply. This is plan item G1.

## The setup

**One service.** The API answers under `/api` and serves the built website at every other address
(`api/trove/serve.py`). The browser sees one address, so there is nothing to configure between a website host
and an API host, and the website's own `/api/...` calls work as they do in development.

- **Host:** [Render](https://render.com), a free web service built from the `Dockerfile` and `render.yaml`
  in the repository root. It gives a free address like `https://trove.onrender.com` with HTTPS.
- **Database:** the existing MongoDB Atlas cluster, in a database of its own (`trove_prod`).
- **Free-tier limits to expect:**
  - The service sleeps after 15 minutes without traffic and takes up to about a minute to wake, so the
    first visitor after a quiet spell waits.
  - Its disk is wiped on every restart. Trove keeps nothing important on disk, except the AI spending
    ledger (see below).

## Who supplies what

Nobody should paste a secret into a chat, a PR or a file in the repository. Each goes into Render's dashboard
(the "Environment" page of the service).

1. **Database (Daniel, for now): his own free Atlas cluster.** This keeps launch data apart from the team's
   shared dev cluster. In Atlas: make a free (M0) cluster; under Database Access add a user for production only,
   limited to the `trove_prod` database, with a long random password (not one used anywhere else); under
   Network Access allow `0.0.0.0/0`, because Render's free service has no fixed address; then copy the
   connection string into Render as `MONGODB_URI`. The app makes its own indexes when it starts, so an empty
   database is all it needs. Moving to a shared cluster later means changing `MONGODB_URI` and moving the data.
2. **AI (Josef): the team's Anthropic key, with his agreement.** It is his account, so the live site spends his
   money, and heavy use by members shares a budget with the team's own development. Before launch, Josef should
   decide:
   - **A spend limit** in the Anthropic console, so a busy week can't run up a bill. Put the key in Render as
     `ANTHROPIC_API_KEY`.
   - `AI_BUDGET_USD` also exists, but its ledger is a file that this host erases on every restart, so it
     can't be the cap. The console limit is.
   - If the key ever leaks, it has to be revoked, which breaks every teammate's `.env` until a new one is
     shared. A key made just for the live site avoids that. This is worth doing before the site has real
     members, but isn't needed for a first test.
   - **There is no free fake-AI mode for launch.** `AI_MODE=scripted` refuses to start anywhere that isn't a
     developer's machine, on purpose, so canned replies can't reach a member.
3. **Email (Daniel).** Students can't confirm their case.edu address, and nobody gets reminders, until `SMTP_*`
   is set. The quickest free option is a new Gmail account made just for Trove (not a personal one) with
   2-step verification on and an [app password](https://support.google.com/accounts/answer/185833):
   `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_USER` the address, `SMTP_PASSWORD` the app password,
   `EMAIL_FROM` like `Trove <that address>`. Gmail allows about 500 emails a day, which is plenty at first.
4. **A Render account (Daniel)** to own the service, signed in with GitHub. Add the others as team members, so
   it doesn't depend on one person.

## Steps

1. In Render, choose **New → Blueprint** and pick this repository. It reads `render.yaml`.
2. Fill in the values Render asks for (the ones above). Leave `FRONTEND_URL` and `API_URL` empty for the first
   deploy.
3. When the first deploy gives the address, set `FRONTEND_URL` to it (`https://trove.onrender.com`) and
   `API_URL` to the same with `/api` on the end, then redeploy. These go into emails (links to the app and the
   unsubscribe link) and invite links.
4. Open the address, sign up with a case.edu email and confirm the code arrives.

## Check this once live

Attempt limits (sign-up, sign-in, codes) are counted per caller address. `TRUSTED_PROXY_HOPS=1` makes the app
read the caller from the end of `X-Forwarded-For`, where Render's load balancer writes it. If it were wrong,
everyone would share one limit (they'd be locked out after a few sign-ups) or one person could dodge it. So,
once:

- Sign in wrongly 11 times from your own browser. The 11th should answer "Too many attempts".
- Then sign in from a different network, such as your phone's data. It should work, since it's another caller.

If the second step is also blocked, the setting is wrong (try `2`, which is right when another proxy sits in
front of Render's); if the first step never blocks, set it to `0` and tell Daniel.

## A better domain, later

A free address from the host is fine to start. To use a real domain, such as a free `.me` from the GitHub Student
Developer Pack, add it in Render under the service's **Custom Domains**, add the DNS records Render shows at the
registrar, and then change `FRONTEND_URL` and `API_URL` to the new address. Links in earlier emails and invites
point at the old one, so do this before sending many.

## Not tested

The `Dockerfile` and `render.yaml` were written without Docker available, so the first deploy is their first
real test. The combined server itself (`trove.serve`) is covered by tests and was run locally against a real
build of the website.
