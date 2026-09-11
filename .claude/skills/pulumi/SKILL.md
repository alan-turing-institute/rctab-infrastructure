---
name: pulumi
description: Use whenever running `pulumi` commands, reading or changing stack config, adding a config variable, or reasoning about which Azure resources a change to this repo will create or destroy. Explains where stack values live (gitignored), which commands are read-only and which mutate real Azure resources, how config flows through constants.py, and the stack-name/ticker and certificate-path gotchas that trial and error would hit.
---

# Pulumi in this repo

This repo *is* a Pulumi program: `Pulumi.yaml` sets `main: rctab_infrastructure/`, so
`pulumi` commands run from the repo root and execute `rctab_infrastructure/__main__.py`.
Full deployment walkthrough: `docs/content/deployment.md` — check it before inventing a
multi-step procedure.

## Read-only vs destructive

Only these are safe to run unprompted:

```shell
pulumi stack ls            # which stacks exist, which is selected
pulumi config              # keys and (masked) values for the selected stack
pulumi preview             # what would change; runs the program, creates nothing
pulumi stack output
```

`pulumi up`, `pulumi destroy`/`down`, `pulumi config set`, `pulumi stack init|rm|rename`
all change real, billable Azure resources or the stack's stored state. Do not run them
unless told to, for that named stack. Take-down, when asked for, is
`pulumi down --continue-on-error`.

## Where config comes from

Each stack's values live in `Pulumi.<stack>.yaml` (e.g. `dev_1`, `dev_2`, `production`, ...),
which is **gitignored** — so the values are not in the repo and must not be guessed or
invented. If something you need is missing, ask the user or have them run `pulumi config`.

`rctab_infrastructure/constants.py` reads all of it at import time through
`pulumi.Config()`. The Pulumi config key is the lowercase form of the Python constant:
`ORGANISATION` ← `organisation`, `AD_TENANT_ID` ← `ad_tenant_id`. Because the reads are
at module import, a missing `require`d key fails immediately on `pulumi preview` with a
`Missing required configuration variable` error — that is a config problem, not a bug in
the program.

Adding a config variable means three edits together:

1. a `config.get(...)`/`config.require_secret(...)` line in `constants.py`, wrapped in
   the relevant validator from `utils.py`;
2. an entry in the `Attributes:` block of the `constants.py` module docstring (Sphinx
   renders it);
3. a section in `docs/content/deployment.md` under Required or Optional Config Variables.

Set secrets with `pulumi config set --secret <key> '<value>'`. Never echo a secret value
back, and never run `pulumi config --show-secrets` just to inspect state.

## Gotchas

- **Check the selected stack before anything else.** `pulumi stack select` is sticky
  state on the machine, not a per-command flag, so an unqualified `pulumi preview` may
  target `prod`. Run `pulumi stack ls` first and pass `--stack <name>` explicitly.
- **`az login` is the user's job.** Pulumi's `azure-native` provider uses the Azure CLI's
  credentials and active subscription. Check read-only with `az account show`; if it
  fails, ask the user to run `az login` — in Claude Code they can run it inline with
  `! az login` — rather than launching an interactive command in an agent shell.
- **Never change the active subscription yourself.** `az account set` is machine-global
  and the current selection may be deliberate. Show the user the mismatch and let them
  decide.
- **Stack name and ticker are immutable after deployment.** Both feed the database server
  name. Renaming a stack after deployment makes Pulumi drop and recreate the server
  without recreating the database user, leaving a broken deployment. Their combined
  length must also be ≤ 10 characters — `validate_ticker_stack_combination` in
  `utils.py` enforces this at preview time.
- **`db_root_cert_path` must point at a file that exists on *this* machine.**
  `assert_is_file` runs during config load, so a stack configured on someone else's
  laptop fails `pulumi preview` locally with a path error that has nothing to do with
  your change. The file is the concatenated Microsoft RSA Root CA 2017 + DigiCert Global
  Root G2 pair (`combined.crt.pem`); see `docs/content/deployment.md`.
- **Secrets are `Output[str]`, not `str`.** `config.require_secret(...)` returns an
  `Output`; f-string interpolation yields `Calling __str__ on an Output[T] is not
  supported` output in the resource rather than the value. Use `.apply(...)`, or
  `Output.all(...)` to combine several.
- **Config edits on the Azure portal are transient.** App settings written by this
  program are overwritten or deleted on the next `pulumi up`. Change them here, not in
  the portal.
- **Post-deployment role assignments are manual.** The Usage and Controller apps need
  roles granted after `pulumi up`; a successful deploy is not a working deploy. See
  "Post Pulumi Deployment" in `docs/content/deployment.md`.
