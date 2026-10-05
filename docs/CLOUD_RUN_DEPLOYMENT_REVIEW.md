# CFP+ Cloud Run conflict review

Status: P0 NOT DONE. Proposed fix requires review and existing-trigger adoption.

## Source and finding

Website: charityfundplus/CFP.plus, main 835616308111f6851c0387fa9f5eda60c9ffa624, existing Nginx Dockerfile.
Gateway/API/MCP: charityfundplus/cfp-gateway, main f530739cf7f53e8b6043d1633a95e27657b58481, separate runtime; unchanged.
Neither inspected main contains cloudbuild.yaml or a Cloud deployment workflow.
Human supplied evidence says Website main built and pushed successfully, but Cloud Run update returned `ABORTED: Conflict for resource 'cfp-plus'`.
This establishes a conflicting update, not the identity of another writer. Failed build ID, trigger IDs, project, regions, service operation history and revision are unavailable. Duplicate triggers, overlapping builds and manual updates remain unverified hypotheses. No Cloud authentication is configured in this execution environment.

## Proposed change

Adopt cloudbuild.yaml on the EXISTING Website main trigger after Human review. Do not add another trigger. Preserve its approved service account and logging configuration. Populate _REGION and _IMAGE_REPOSITORY from actual Cloud inventory; empty defaults deliberately fail closed. Gateway must retain its own independently verified service target.

Build and push a BUILD_ID tag, obtain its immutable digest, update the existing cfp-plus service only. Queue older active builds in the same project/build region/_SERVICE; retry only ABORTED conflicts, with bounded backoff. Deny missing source/configuration, non-main builds and non-Website service targets. Require Ready revision and matching image, but explicitly record HTTP readback as NOT_RUN.

Queue coordination is NOT a distributed lock across manual writers, other regions, triggers without _SERVICE or eventual-consistency races. Inventory and consolidate all deployment writers before adoption. Retry mitigates transient conflicts; actual Cloud verification must establish whether it resolves the reported incident.

No service creation/deletion, IAM/environment/secrets rewrite, DID/lineage changes or Canonical Lock. PR workflow tests only and never deploys. Do not interpret service readiness as website/API readback PASS.

## Verification and evidence

Commands: python -m unittest discover -s tests/pipeline -v; python run_ctttc_v066_tests.py; python tests/ctttc/duplicate_unicode_regression_v066.py; python -m py_compile scripts/deploy_cloud_run.py; git diff --check; YAML step/dependency validation; local Docker build where available.
Final commands, outputs and Git HEAD are recorded externally under /workspace/cfp-review/evidence/pipeline-conflict to avoid self-referential commit evidence. Unit tests mock Cloud operations and cannot prove Cloud Build, deployment or production health.

## Minimum access and Human actions

Authenticate a scoped Google Cloud identity and provide project ID, Cloud Build region, Cloud Run region and failed Build ID. Read-only inventory: roles/cloudbuild.builds.viewer and roles/run.viewer; roles/logging.viewer only if logs are needed; roles/artifactregistry.reader on the existing repository for digest inspection. No Owner role needed. There is currently no IAM rejection establishing which permission the existing deployment account lacks.

Review/merge PR separately. An authorized operator must inventory triggers/writers and point the existing Website trigger to this file, preserving approved identity/log settings and configuring existing region/image path. Trigger update requires cloudbuild.triggers.get/list/update (a scoped custom role if appropriate). Deployment account needs builds.list for queue visibility, run.services.get/update and operations.get, artifact upload permission, and iam.serviceAccounts.actAs only on the existing runtime identity when required. Typical scoped roles: Cloud Build Viewer, Cloud Run Developer, Artifact Registry Writer, Service Account User; verify existing grants before adding any.

Run the reviewed main trigger, record Build ID, source SHA and image digest, ready revision, actual traffic, health endpoint and numeric Website readback. Inspect API through its actual Gateway binding. Never invent an API route or target. For rollback, retain previous source/image/revision; Human-approved restoration updates the existing service to the previous immutable digest and preserves its approved traffic configuration. No database migration, DNS or secret changes.

Recommend main branch PR review and required CI checks after checking operational impact; do not alter protection in this work order.
