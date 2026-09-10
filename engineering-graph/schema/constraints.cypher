CREATE CONSTRAINT requirement_identity IF NOT EXISTS FOR (n:Requirement) REQUIRE (n.repository, n.canonicalId) IS UNIQUE;
CREATE CONSTRAINT spec_identity IF NOT EXISTS FOR (n:Spec) REQUIRE (n.repository, n.canonicalId) IS UNIQUE;
CREATE CONSTRAINT adr_identity IF NOT EXISTS FOR (n:ADR) REQUIRE (n.repository, n.canonicalId) IS UNIQUE;
CREATE CONSTRAINT task_identity IF NOT EXISTS FOR (n:Task) REQUIRE (n.repository, n.canonicalId) IS UNIQUE;
CREATE CONSTRAINT code_artifact_identity IF NOT EXISTS FOR (n:CodeArtifact) REQUIRE (n.repository, n.canonicalId) IS UNIQUE;
CREATE CONSTRAINT test_identity IF NOT EXISTS FOR (n:Test) REQUIRE (n.repository, n.canonicalId) IS UNIQUE;
CREATE CONSTRAINT pull_request_identity IF NOT EXISTS FOR (n:PullRequest) REQUIRE (n.repository, n.canonicalId) IS UNIQUE;

CREATE INDEX task_status IF NOT EXISTS FOR (n:Task) ON (n.repository, n.status);
CREATE INDEX task_spec IF NOT EXISTS FOR (n:Task) ON (n.repository, n.specId);
CREATE INDEX spec_status IF NOT EXISTS FOR (n:Spec) ON (n.repository, n.status);
CREATE INDEX code_artifact_path IF NOT EXISTS FOR (n:CodeArtifact) ON (n.repository, n.path);
CREATE INDEX test_path IF NOT EXISTS FOR (n:Test) ON (n.repository, n.path);
CREATE INDEX pull_request_number IF NOT EXISTS FOR (n:PullRequest) ON (n.repository, n.number);
