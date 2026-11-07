## 1. Annotations

- [x] 1.1 Add the annotations to both tools and test that a client sees them

## 2. HTTP transport

- [x] 2.1 Add the optional streamable-HTTP transport, loopback by default, selected by configuration
- [x] 2.2 Require a bearer token on a non-loopback address and refuse to start without it
- [x] 2.3 Test authentication: missing token, wrong token, right token, constant-time comparison, no token in logs or errors, and that stdio is unchanged

## 3. Container

- [x] 3.1 Add the Dockerfile (non-root, no secrets) and a CI step that builds it
- [x] 3.2 Run the image once against a live normkompass and record the date and result in the README

## 4. Docs and wrap-up

- [x] 4.1 Update the README: transports, the token rule, the container, and that a public deployment is unsupported and why
- [x] 4.2 Run `openspec archive transport-and-packaging` and keep the Purpose sections filled
