# agentactioncapsule-site

Static site for **agentactioncapsule.org** — the neutral IETF standard page for the Agent Action
Capsule profile, plus the HashiCorp-style concept/docs layer.

Self-contained HTML, served by nginx:alpine on port 8080. **No build step at deploy** — the docs
pages are pre-generated static files.

```
index.html              The standard landing (apex)
docs/index.html         Docs overview
docs/*.html             8 concept/guide/reference pages
tools/build_docs.py     Docs generator (authoring-time only; emits docs/*.html)
Dockerfile, nginx.conf  nginx:alpine static container, port 8080
robots.txt, sitemap.xml
LICENSE, NOTICE         Apache-2.0
```

Neutral substrate: no product / moat / Authority / tiering / monetization language. The three
neutral surfaces (this site, `anchor.agentactioncapsule.org`, `verify.actionstate.ai`) share one
visual system and a common cross-site nav + footer.

## Run locally

```sh
docker build -t agentactioncapsule-site .
docker run --rm -p 8080:8080 agentactioncapsule-site
curl -I http://localhost:8080/            # 200
curl -I http://localhost:8080/docs/       # 200
curl -I http://localhost:8080/docs/glossary.html   # 200
```

## Editing the docs

Edit content in `tools/build_docs.py` (the `PAGES` dict + `INDEX_BODY`), then regenerate:

```sh
python3 tools/build_docs.py     # rewrites docs/*.html
```

## Deploy to Cloud Run (gated — Steven only)

```sh
# from this directory:
gcloud run deploy agentactioncapsule-site \
  --project fluxxom \
  --region us-central1 \
  --source . \
  --allow-unauthenticated

# map the apex domain (already verified in fluxxom):
gcloud beta run domain-mappings create \
  --service agentactioncapsule-site \
  --domain agentactioncapsule.org \
  --region us-central1 \
  --project fluxxom
```

After the domain mapping, Google returns A/AAAA records (`rrdata`). Add those as **A** and **AAAA**
records for `agentactioncapsule.org` in Bluehost DNS (no www needed for the apex mapping). HTTPS
cert is auto-provisioned once DNS resolves.

> Repo-name note: the brief calls the public repo `agentactioncapsule-web`; this staging folder and
> the Cloud Run **service** are named `agentactioncapsule-site` (from the earlier Part-2 work). The
> service name and the GitHub repo name don't have to match — confirm the GitHub repo name at
> creation time.

## Standards status

`draft-mih-scitt-agent-action-capsule` is an **individual** IETF Internet-Draft — not WG-adopted,
not a standard. SCITT/COSE specs are drafts, **not yet RFCs**. RFC 9162 is a published RFC.

## License

Apache-2.0. See `LICENSE` and `NOTICE`.
