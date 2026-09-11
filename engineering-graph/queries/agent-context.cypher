MATCH (task:Task {repository: $repository, canonicalId: $taskId})
OPTIONAL MATCH (spec:Spec {repository: $repository})-[:DECOMPOSED_INTO]->(task)
OPTIONAL MATCH (requirement:Requirement {repository: $repository})-[:REALIZED_BY]->(spec)
OPTIONAL MATCH (spec)-[:CONSTRAINED_BY]->(adr:ADR {repository: $repository})
OPTIONAL MATCH (task)-[:DEPENDS_ON]->(dependency:Task {repository: $repository})
OPTIONAL MATCH (task)-[:IMPLEMENTED_BY]->(code:CodeArtifact {repository: $repository})
OPTIONAL MATCH (task)-[:VALIDATED_BY]->(test:Test {repository: $repository})
OPTIONAL MATCH (pr:PullRequest {repository: $repository})-[:IMPLEMENTS]->(task)
RETURN task {
         .canonicalId, .sourceId, .title, .status, .priority, .parallel,
         .userStory, .phase, .sourcePath, .line, .specId, .sourceRevision
       } AS task,
       task.sourceRevision AS sourceRevision,
       spec {
         .canonicalId, .featureId, .slug, .title, .status,
         .sourcePath, .enforced, .sourceRevision
       } AS spec,
       collect(DISTINCT requirement {
         .canonicalId, .sourceId, .kind, .text, .critical,
         .sourcePath, .line, .sourceRevision
       }) AS requirements,
       collect(DISTINCT adr {
         .canonicalId, .number, .title, .status, .sourcePath, .sourceRevision
       }) AS adrs,
       collect(DISTINCT dependency {
         .canonicalId, .sourceId, .title, .status, .priority, .parallel,
         .userStory, .phase, .sourcePath, .line, .specId, .sourceRevision
       }) AS dependencies,
       collect(DISTINCT code {
         .canonicalId, .path, .kind, .exists, .sourceRevision
       }) AS code,
       collect(DISTINCT test {
         .canonicalId, .path, .kind, .exists, .sourceRevision
       }) AS tests,
       collect(DISTINCT pr {
         .canonicalId, .number, .title, .state, .url,
         .headSha, .baseSha, .source, .sourceRevision
       }) AS pullRequests
