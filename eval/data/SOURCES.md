# Data sources

`failures.jsonl` holds 196 real failed jobs from public GitHub Actions runs of 61 repositories licensed
MIT or Apache-2.0 (the licence GitHub reports for each repository), and 4 invented excerpts marked `"invented": true`. Each real record links to its run and job (`run_url`, `job_url`).
Logs were fetched with `gh api` (`scripts/harvest.py`), trimmed to the region around the first failure by
`ci_triage/logs.py` and passed through the secret and e-mail redactor in `ci_triage/redact.py` before being stored.
Excerpts are quoted unchanged apart from trimming and redaction, under each project's licence.

| Repository | Licence | Failed jobs |
|---|---|---|
| [apache/airflow](https://github.com/apache/airflow) | Apache-2.0 | 2 |
| [apache/arrow](https://github.com/apache/arrow) | Apache-2.0 | 3 |
| [apache/datafusion](https://github.com/apache/datafusion) | Apache-2.0 | 2 |
| [apache/iceberg](https://github.com/apache/iceberg) | Apache-2.0 | 2 |
| [apache/pulsar](https://github.com/apache/pulsar) | Apache-2.0 | 4 |
| [argoproj/argo-cd](https://github.com/argoproj/argo-cd) | Apache-2.0 | 2 |
| [astral-sh/ruff](https://github.com/astral-sh/ruff) | MIT | 3 |
| [astral-sh/uv](https://github.com/astral-sh/uv) | Apache-2.0 | 5 |
| [aws/aws-cdk](https://github.com/aws/aws-cdk) | Apache-2.0 | 1 |
| [backstage/backstage](https://github.com/backstage/backstage) | Apache-2.0 | 2 |
| [biomejs/biome](https://github.com/biomejs/biome) | Apache-2.0 | 4 |
| [caddyserver/caddy](https://github.com/caddyserver/caddy) | Apache-2.0 | 1 |
| [cli/cli](https://github.com/cli/cli) | MIT | 2 |
| [containerd/containerd](https://github.com/containerd/containerd) | Apache-2.0 | 6 |
| [dagster-io/dagster](https://github.com/dagster-io/dagster) | Apache-2.0 | 1 |
| [denoland/deno](https://github.com/denoland/deno) | MIT | 4 |
| [docker/compose](https://github.com/docker/compose) | Apache-2.0 | 2 |
| [duckdb/duckdb](https://github.com/duckdb/duckdb) | MIT | 4 |
| [eslint/eslint](https://github.com/eslint/eslint) | MIT | 7 |
| [etcd-io/etcd](https://github.com/etcd-io/etcd) | Apache-2.0 | 1 |
| [excalidraw/excalidraw](https://github.com/excalidraw/excalidraw) | MIT | 2 |
| [facebook/react](https://github.com/facebook/react) | MIT | 2 |
| [fastapi/fastapi](https://github.com/fastapi/fastapi) | MIT | 2 |
| [fastify/fastify](https://github.com/fastify/fastify) | MIT | 4 |
| [go-gitea/gitea](https://github.com/go-gitea/gitea) | MIT | 3 |
| [helm/helm](https://github.com/helm/helm) | Apache-2.0 | 2 |
| [home-assistant/core](https://github.com/home-assistant/core) | Apache-2.0 | 3 |
| [huggingface/transformers](https://github.com/huggingface/transformers) | Apache-2.0 | 2 |
| [keycloak/keycloak](https://github.com/keycloak/keycloak) | Apache-2.0 | 2 |
| [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | MIT | 3 |
| [microsoft/playwright](https://github.com/microsoft/playwright) | Apache-2.0 | 3 |
| [microsoft/TypeScript](https://github.com/microsoft/TypeScript) | Apache-2.0 | 9 |
| [moby/moby](https://github.com/moby/moby) | Apache-2.0 | 2 |
| [mui/material-ui](https://github.com/mui/material-ui) | MIT | 4 |
| [nestjs/nest](https://github.com/nestjs/nest) | MIT | 1 |
| [nodejs/undici](https://github.com/nodejs/undici) | MIT | 4 |
| [ollama/ollama](https://github.com/ollama/ollama) | MIT | 3 |
| [open-telemetry/opentelemetry-collector-contrib](https://github.com/open-telemetry/opentelemetry-collector-contrib) | Apache-2.0 | 4 |
| [open-telemetry/opentelemetry-python](https://github.com/open-telemetry/opentelemetry-python) | Apache-2.0 | 1 |
| [opensearch-project/OpenSearch](https://github.com/opensearch-project/OpenSearch) | Apache-2.0 | 3 |
| [pnpm/pnpm](https://github.com/pnpm/pnpm) | MIT | 3 |
| [pola-rs/polars](https://github.com/pola-rs/polars) | MIT | 5 |
| [prettier/prettier](https://github.com/prettier/prettier) | MIT | 2 |
| [prisma/prisma](https://github.com/prisma/prisma) | Apache-2.0 | 6 |
| [prometheus/prometheus](https://github.com/prometheus/prometheus) | Apache-2.0 | 3 |
| [pulumi/pulumi](https://github.com/pulumi/pulumi) | Apache-2.0 | 5 |
| [pydantic/pydantic](https://github.com/pydantic/pydantic) | MIT | 4 |
| [quarkusio/quarkus](https://github.com/quarkusio/quarkus) | Apache-2.0 | 2 |
| [storybookjs/storybook](https://github.com/storybookjs/storybook) | MIT | 3 |
| [supabase/supabase](https://github.com/supabase/supabase) | Apache-2.0 | 2 |
| [sveltejs/svelte](https://github.com/sveltejs/svelte) | MIT | 6 |
| [tauri-apps/tauri](https://github.com/tauri-apps/tauri) | Apache-2.0 | 1 |
| [tokio-rs/tokio](https://github.com/tokio-rs/tokio) | MIT | 9 |
| [traefik/traefik](https://github.com/traefik/traefik) | MIT | 1 |
| [trinodb/trino](https://github.com/trinodb/trino) | Apache-2.0 | 4 |
| [typescript-eslint/typescript-eslint](https://github.com/typescript-eslint/typescript-eslint) | MIT | 5 |
| [vercel/next.js](https://github.com/vercel/next.js) | MIT | 5 |
| [vitejs/vite](https://github.com/vitejs/vite) | MIT | 4 |
| [vitest-dev/vitest](https://github.com/vitest-dev/vitest) | MIT | 3 |
| [vllm-project/vllm](https://github.com/vllm-project/vllm) | Apache-2.0 | 3 |
| [vuejs/core](https://github.com/vuejs/core) | MIT | 3 |

## Runs

- `apache__airflow__114677477611`: [run](https://github.com/apache/airflow/actions/runs/38208588650), [job](https://github.com/apache/airflow/actions/runs/38208588650/job/114677477611) (Apache-2.0)
- `apache__airflow__114679260679`: [run](https://github.com/apache/airflow/actions/runs/38208585723), [job](https://github.com/apache/airflow/actions/runs/38208585723/job/114679260679) (Apache-2.0)
- `apache__arrow__114279182920`: [run](https://github.com/apache/arrow/actions/runs/38074700175), [job](https://github.com/apache/arrow/actions/runs/38074700175/job/114279182920) (Apache-2.0)
- `apache__arrow__114627462426`: [run](https://github.com/apache/arrow/actions/runs/38192303422), [job](https://github.com/apache/arrow/actions/runs/38192303422/job/114627462426) (Apache-2.0)
- `apache__arrow__114696873411`: [run](https://github.com/apache/arrow/actions/runs/38214620842), [job](https://github.com/apache/arrow/actions/runs/38214620842/job/114696873411) (Apache-2.0)
- `apache__datafusion__114499424109`: [run](https://github.com/apache/datafusion/actions/runs/38148986187), [job](https://github.com/apache/datafusion/actions/runs/38148986187/job/114499424109) (Apache-2.0)
- `apache__datafusion__114660866965`: [run](https://github.com/apache/datafusion/actions/runs/38202271883), [job](https://github.com/apache/datafusion/actions/runs/38202271883/job/114660866965) (Apache-2.0)
- `apache__iceberg__114652635228`: [run](https://github.com/apache/iceberg/actions/runs/38200507750), [job](https://github.com/apache/iceberg/actions/runs/38200507750/job/114652635228) (Apache-2.0)
- `apache__iceberg__114671426962`: [run](https://github.com/apache/iceberg/actions/runs/38206626914), [job](https://github.com/apache/iceberg/actions/runs/38206626914/job/114671426962) (Apache-2.0)
- `apache__pulsar__112905645989`: [run](https://github.com/apache/pulsar/actions/runs/37652808414), [job](https://github.com/apache/pulsar/actions/runs/37652808414/job/112905645989) (Apache-2.0)
- `apache__pulsar__114033696031`: [run](https://github.com/apache/pulsar/actions/runs/37900772406), [job](https://github.com/apache/pulsar/actions/runs/37900772406/job/114033696031) (Apache-2.0)
- `apache__pulsar__114379871197`: [run](https://github.com/apache/pulsar/actions/runs/38108389914), [job](https://github.com/apache/pulsar/actions/runs/38108389914/job/114379871197) (Apache-2.0)
- `apache__pulsar__114413706398`: [run](https://github.com/apache/pulsar/actions/runs/38116754475), [job](https://github.com/apache/pulsar/actions/runs/38116754475/job/114413706398) (Apache-2.0)
- `argoproj__argo-cd__114710715153`: [run](https://github.com/argoproj/argo-cd/actions/runs/38218864724), [job](https://github.com/argoproj/argo-cd/actions/runs/38218864724/job/114710715153) (Apache-2.0)
- `argoproj__argo-cd__114711845030`: [run](https://github.com/argoproj/argo-cd/actions/runs/38219362579), [job](https://github.com/argoproj/argo-cd/actions/runs/38219362579/job/114711845030) (Apache-2.0)
- `astral-sh__ruff__113780390598`: [run](https://github.com/astral-sh/ruff/actions/runs/37918445241), [job](https://github.com/astral-sh/ruff/actions/runs/37918445241/job/113780390598) (MIT)
- `astral-sh__ruff__113991207459`: [run](https://github.com/astral-sh/ruff/actions/runs/37980192578), [job](https://github.com/astral-sh/ruff/actions/runs/37980192578/job/113991207459) (MIT)
- `astral-sh__ruff__114006374173`: [run](https://github.com/astral-sh/ruff/actions/runs/37985467505), [job](https://github.com/astral-sh/ruff/actions/runs/37985467505/job/114006374173) (MIT)
- `astral-sh__uv__113930417049`: [run](https://github.com/astral-sh/uv/actions/runs/37962959153), [job](https://github.com/astral-sh/uv/actions/runs/37962959153/job/113930417049) (Apache-2.0)
- `astral-sh__uv__114039153490`: [run](https://github.com/astral-sh/uv/actions/runs/37994770690), [job](https://github.com/astral-sh/uv/actions/runs/37994770690/job/114039153490) (Apache-2.0)
- `astral-sh__uv__114212970287`: [run](https://github.com/astral-sh/uv/actions/runs/38051810819), [job](https://github.com/astral-sh/uv/actions/runs/38051810819/job/114212970287) (Apache-2.0)
- `astral-sh__uv__114471066139`: [run](https://github.com/astral-sh/uv/actions/runs/38139553647), [job](https://github.com/astral-sh/uv/actions/runs/38139553647/job/114471066139) (Apache-2.0)
- `astral-sh__uv__114473800162`: [run](https://github.com/astral-sh/uv/actions/runs/38140632364), [job](https://github.com/astral-sh/uv/actions/runs/38140632364/job/114473800162) (Apache-2.0)
- `aws__aws-cdk__114434629617`: [run](https://github.com/aws/aws-cdk/actions/runs/38127439766), [job](https://github.com/aws/aws-cdk/actions/runs/38127439766/job/114434629617) (Apache-2.0)
- `backstage__backstage__113821261174`: [run](https://github.com/backstage/backstage/actions/runs/37930958298), [job](https://github.com/backstage/backstage/actions/runs/37930958298/job/113821261174) (Apache-2.0)
- `backstage__backstage__114625705553`: [run](https://github.com/backstage/backstage/actions/runs/38191612165), [job](https://github.com/backstage/backstage/actions/runs/38191612165/job/114625705553) (Apache-2.0)
- `biomejs__biome__114420520834`: [run](https://github.com/biomejs/biome/actions/runs/38122693499), [job](https://github.com/biomejs/biome/actions/runs/38122693499/job/114420520834) (Apache-2.0)
- `biomejs__biome__114461688832`: [run](https://github.com/biomejs/biome/actions/runs/38136618022), [job](https://github.com/biomejs/biome/actions/runs/38136618022/job/114461688832) (Apache-2.0)
- `biomejs__biome__114559444722`: [run](https://github.com/biomejs/biome/actions/runs/38169670283), [job](https://github.com/biomejs/biome/actions/runs/38169670283/job/114559444722) (Apache-2.0)
- `biomejs__biome__114701802800`: [run](https://github.com/biomejs/biome/actions/runs/38216324499), [job](https://github.com/biomejs/biome/actions/runs/38216324499/job/114701802800) (Apache-2.0)
- `caddyserver__caddy__114633314751`: [run](https://github.com/caddyserver/caddy/actions/runs/38194243813), [job](https://github.com/caddyserver/caddy/actions/runs/38194243813/job/114633314751) (Apache-2.0)
- `cli__cli__113566862286`: [run](https://github.com/cli/cli/actions/runs/37851984062), [job](https://github.com/cli/cli/actions/runs/37851984062/job/113566862286) (MIT)
- `cli__cli__113856281888`: [run](https://github.com/cli/cli/actions/runs/37941363988), [job](https://github.com/cli/cli/actions/runs/37941363988/job/113856281888) (MIT)
- `containerd__containerd__113254204615`: [run](https://github.com/containerd/containerd/actions/runs/37760119173), [job](https://github.com/containerd/containerd/actions/runs/37760119173/job/113254204615) (Apache-2.0)
- `containerd__containerd__114023169987`: [run](https://github.com/containerd/containerd/actions/runs/37990514510), [job](https://github.com/containerd/containerd/actions/runs/37990514510/job/114023169987) (Apache-2.0)
- `containerd__containerd__114024268752`: [run](https://github.com/containerd/containerd/actions/runs/37990514690), [job](https://github.com/containerd/containerd/actions/runs/37990514690/job/114024268752) (Apache-2.0)
- `containerd__containerd__114468134080`: [run](https://github.com/containerd/containerd/actions/runs/38138592265), [job](https://github.com/containerd/containerd/actions/runs/38138592265/job/114468134080) (Apache-2.0)
- `containerd__containerd__114636614347`: [run](https://github.com/containerd/containerd/actions/runs/38195332737), [job](https://github.com/containerd/containerd/actions/runs/38195332737/job/114636614347) (Apache-2.0)
- `containerd__containerd__114699632273`: [run](https://github.com/containerd/containerd/actions/runs/38215348972), [job](https://github.com/containerd/containerd/actions/runs/38215348972/job/114699632273) (Apache-2.0)
- `dagster-io__dagster__114393313886`: [run](https://github.com/dagster-io/dagster/actions/runs/38113361720), [job](https://github.com/dagster-io/dagster/actions/runs/38113361720/job/114393313886) (Apache-2.0)
- `denoland__deno__108160114303`: [run](https://github.com/denoland/deno/actions/runs/36161842150), [job](https://github.com/denoland/deno/actions/runs/36161842150/job/108160114303) (MIT)
- `denoland__deno__111700926828`: [run](https://github.com/denoland/deno/actions/runs/37290333324), [job](https://github.com/denoland/deno/actions/runs/37290333324/job/111700926828) (MIT)
- `denoland__deno__112193005528`: [run](https://github.com/denoland/deno/actions/runs/37440538664), [job](https://github.com/denoland/deno/actions/runs/37440538664/job/112193005528) (MIT)
- `denoland__deno__112194068168`: [run](https://github.com/denoland/deno/actions/runs/37440854618), [job](https://github.com/denoland/deno/actions/runs/37440854618/job/112194068168) (MIT)
- `docker__compose__113305180634`: [run](https://github.com/docker/compose/actions/runs/37775498854), [job](https://github.com/docker/compose/actions/runs/37775498854/job/113305180634) (Apache-2.0)
- `docker__compose__113729500586`: [run](https://github.com/docker/compose/actions/runs/37902896379), [job](https://github.com/docker/compose/actions/runs/37902896379/job/113729500586) (Apache-2.0)
- `duckdb__duckdb__114596371577`: [run](https://github.com/duckdb/duckdb/actions/runs/38181943788), [job](https://github.com/duckdb/duckdb/actions/runs/38181943788/job/114596371577) (MIT)
- `duckdb__duckdb__114617439999`: [run](https://github.com/duckdb/duckdb/actions/runs/38186180789), [job](https://github.com/duckdb/duckdb/actions/runs/38186180789/job/114617439999) (MIT)
- `duckdb__duckdb__114623572881`: [run](https://github.com/duckdb/duckdb/actions/runs/38191010491), [job](https://github.com/duckdb/duckdb/actions/runs/38191010491/job/114623572881) (MIT)
- `duckdb__duckdb__114706567007`: [run](https://github.com/duckdb/duckdb/actions/runs/38217552462), [job](https://github.com/duckdb/duckdb/actions/runs/38217552462/job/114706567007) (MIT)
- `eslint__eslint__107914002320`: [run](https://github.com/eslint/eslint/actions/runs/36084748182), [job](https://github.com/eslint/eslint/actions/runs/36084748182/job/107914002320) (MIT)
- `eslint__eslint__108739597333`: [run](https://github.com/eslint/eslint/actions/runs/36361558468), [job](https://github.com/eslint/eslint/actions/runs/36361558468/job/108739597333) (MIT)
- `eslint__eslint__110546824209`: [run](https://github.com/eslint/eslint/actions/runs/36915041555), [job](https://github.com/eslint/eslint/actions/runs/36915041555/job/110546824209) (MIT)
- `eslint__eslint__112349510097`: [run](https://github.com/eslint/eslint/actions/runs/37486997319), [job](https://github.com/eslint/eslint/actions/runs/37486997319/job/112349510097) (MIT)
- `eslint__eslint__112349519907`: [run](https://github.com/eslint/eslint/actions/runs/37487000067), [job](https://github.com/eslint/eslint/actions/runs/37487000067/job/112349519907) (MIT)
- `eslint__eslint__114594430047`: [run](https://github.com/eslint/eslint/actions/runs/38181363682), [job](https://github.com/eslint/eslint/actions/runs/38181363682/job/114594430047) (MIT)
- `eslint__eslint__114612362833`: [run](https://github.com/eslint/eslint/actions/runs/38187322244), [job](https://github.com/eslint/eslint/actions/runs/38187322244/job/114612362833) (MIT)
- `etcd-io__etcd__114621316205`: [run](https://github.com/etcd-io/etcd/actions/runs/38190268571), [job](https://github.com/etcd-io/etcd/actions/runs/38190268571/job/114621316205) (Apache-2.0)
- `excalidraw__excalidraw__109421832804`: [run](https://github.com/excalidraw/excalidraw/actions/runs/36573133624), [job](https://github.com/excalidraw/excalidraw/actions/runs/36573133624/job/109421832804) (MIT)
- `excalidraw__excalidraw__113204016034`: [run](https://github.com/excalidraw/excalidraw/actions/runs/37744920801), [job](https://github.com/excalidraw/excalidraw/actions/runs/37744920801/job/113204016034) (MIT)
- `facebook__react__114442353068`: [run](https://github.com/react/react/actions/runs/38130034916), [job](https://github.com/react/react/actions/runs/38130034916/job/114442353068) (MIT)
- `facebook__react__114611118245`: [run](https://github.com/react/react/actions/runs/38186749956), [job](https://github.com/react/react/actions/runs/38186749956/job/114611118245) (MIT)
- `fastapi__fastapi__112431341271`: [run](https://github.com/fastapi/fastapi/actions/runs/37510846343), [job](https://github.com/fastapi/fastapi/actions/runs/37510846343/job/112431341271) (MIT)
- `fastapi__fastapi__113022199418`: [run](https://github.com/fastapi/fastapi/actions/runs/37688429128), [job](https://github.com/fastapi/fastapi/actions/runs/37688429128/job/113022199418) (MIT)
- `fastify__fastify__114216081544`: [run](https://github.com/fastify/fastify/actions/runs/38052922818), [job](https://github.com/fastify/fastify/actions/runs/38052922818/job/114216081544) (MIT)
- `fastify__fastify__114418620575`: [run](https://github.com/fastify/fastify/actions/runs/38122049976), [job](https://github.com/fastify/fastify/actions/runs/38122049976/job/114418620575) (MIT)
- `fastify__fastify__114420215061`: [run](https://github.com/fastify/fastify/actions/runs/38122588355), [job](https://github.com/fastify/fastify/actions/runs/38122588355/job/114420215061) (MIT)
- `fastify__fastify__114717316264`: [run](https://github.com/fastify/fastify/actions/runs/38221008430), [job](https://github.com/fastify/fastify/actions/runs/38221008430/job/114717316264) (MIT)
- `go-gitea__gitea__114207029579`: [run](https://github.com/go-gitea/gitea/actions/runs/38049988663), [job](https://github.com/go-gitea/gitea/actions/runs/38049988663/job/114207029579) (MIT)
- `go-gitea__gitea__114428501143`: [run](https://github.com/go-gitea/gitea/actions/runs/38125356098), [job](https://github.com/go-gitea/gitea/actions/runs/38125356098/job/114428501143) (MIT)
- `go-gitea__gitea__114458242768`: [run](https://github.com/go-gitea/gitea/actions/runs/38135411512), [job](https://github.com/go-gitea/gitea/actions/runs/38135411512/job/114458242768) (MIT)
- `helm__helm__112010665299`: [run](https://github.com/helm/helm/actions/runs/37383388520), [job](https://github.com/helm/helm/actions/runs/37383388520/job/112010665299) (Apache-2.0)
- `helm__helm__114611997991`: [run](https://github.com/helm/helm/actions/runs/38187200395), [job](https://github.com/helm/helm/actions/runs/38187200395/job/114611997991) (Apache-2.0)
- `home-assistant__core__114700722107`: [run](https://github.com/home-assistant/core/actions/runs/38215880374), [job](https://github.com/home-assistant/core/actions/runs/38215880374/job/114700722107) (Apache-2.0)
- `home-assistant__core__114710827627`: [run](https://github.com/home-assistant/core/actions/runs/38219094090), [job](https://github.com/home-assistant/core/actions/runs/38219094090/job/114710827627) (Apache-2.0)
- `home-assistant__core__114713158394`: [run](https://github.com/home-assistant/core/actions/runs/38219743096), [job](https://github.com/home-assistant/core/actions/runs/38219743096/job/114713158394) (Apache-2.0)
- `huggingface__transformers__114639699626`: [run](https://github.com/huggingface/transformers/actions/runs/38196334678), [job](https://github.com/huggingface/transformers/actions/runs/38196334678/job/114639699626) (Apache-2.0)
- `huggingface__transformers__114644814970`: [run](https://github.com/huggingface/transformers/actions/runs/38197971471), [job](https://github.com/huggingface/transformers/actions/runs/38197971471/job/114644814970) (Apache-2.0)
- `keycloak__keycloak__114477086147`: [run](https://github.com/keycloak/keycloak/actions/runs/38141818603), [job](https://github.com/keycloak/keycloak/actions/runs/38141818603/job/114477086147) (Apache-2.0)
- `keycloak__keycloak__114661729433`: [run](https://github.com/keycloak/keycloak/actions/runs/38203189251), [job](https://github.com/keycloak/keycloak/actions/runs/38203189251/job/114661729433) (Apache-2.0)
- `langchain-ai__langchain__114425207752`: [run](https://github.com/langchain-ai/langchain/actions/runs/38124247886), [job](https://github.com/langchain-ai/langchain/actions/runs/38124247886/job/114425207752) (MIT)
- `langchain-ai__langchain__114497222589`: [run](https://github.com/langchain-ai/langchain/actions/runs/38148644755), [job](https://github.com/langchain-ai/langchain/actions/runs/38148644755/job/114497222589) (MIT)
- `langchain-ai__langchain__114715420249`: [run](https://github.com/langchain-ai/langchain/actions/runs/38220532621), [job](https://github.com/langchain-ai/langchain/actions/runs/38220532621/job/114715420249) (MIT)
- `microsoft__playwright__113558095023`: [run](https://github.com/microsoft/playwright/actions/runs/37849345622), [job](https://github.com/microsoft/playwright/actions/runs/37849345622/job/113558095023) (Apache-2.0)
- `microsoft__playwright__114595100059`: [run](https://github.com/microsoft/playwright/actions/runs/38181583280), [job](https://github.com/microsoft/playwright/actions/runs/38181583280/job/114595100059) (Apache-2.0)
- `microsoft__playwright__114595102329`: [run](https://github.com/microsoft/playwright/actions/runs/38181584088), [job](https://github.com/microsoft/playwright/actions/runs/38181584088/job/114595102329) (Apache-2.0)
- `microsoft__TypeScript__113018896762`: [run](https://github.com/microsoft/TypeScript/actions/runs/37687473973), [job](https://github.com/microsoft/TypeScript/actions/runs/37687473973/job/113018896762) (Apache-2.0)
- `microsoft__TypeScript__113056728582`: [run](https://github.com/microsoft/TypeScript/actions/runs/37698719983), [job](https://github.com/microsoft/TypeScript/actions/runs/37698719983/job/113056728582) (Apache-2.0)
- `microsoft__TypeScript__113177284640`: [run](https://github.com/microsoft/TypeScript/actions/runs/37734512400), [job](https://github.com/microsoft/TypeScript/actions/runs/37734512400/job/113177284640) (Apache-2.0)
- `microsoft__TypeScript__113392742281`: [run](https://github.com/microsoft/TypeScript/actions/runs/37800962639), [job](https://github.com/microsoft/TypeScript/actions/runs/37800962639/job/113392742281) (Apache-2.0)
- `microsoft__TypeScript__113392742922`: [run](https://github.com/microsoft/TypeScript/actions/runs/37800962660), [job](https://github.com/microsoft/TypeScript/actions/runs/37800962660/job/113392742922) (Apache-2.0)
- `microsoft__TypeScript__113527786323`: [run](https://github.com/microsoft/TypeScript/actions/runs/37840331012), [job](https://github.com/microsoft/TypeScript/actions/runs/37840331012/job/113527786323) (Apache-2.0)
- `microsoft__TypeScript__113559811242`: [run](https://github.com/microsoft/TypeScript/actions/runs/37849859691), [job](https://github.com/microsoft/TypeScript/actions/runs/37849859691/job/113559811242) (Apache-2.0)
- `microsoft__TypeScript__114661743121`: [run](https://github.com/microsoft/TypeScript/actions/runs/38201763342), [job](https://github.com/microsoft/TypeScript/actions/runs/38201763342/job/114661743121) (Apache-2.0)
- `microsoft__TypeScript__114673473649`: [run](https://github.com/microsoft/TypeScript/actions/runs/38207286285), [job](https://github.com/microsoft/TypeScript/actions/runs/38207286285/job/114673473649) (Apache-2.0)
- `moby__moby__113824230454`: [run](https://github.com/moby/moby/actions/runs/37930535781), [job](https://github.com/moby/moby/actions/runs/37930535781/job/113824230454) (Apache-2.0)
- `moby__moby__114683870260`: [run](https://github.com/moby/moby/actions/runs/38210671347), [job](https://github.com/moby/moby/actions/runs/38210671347/job/114683870260) (Apache-2.0)
- `mui__material-ui__113816673849`: [run](https://github.com/mui/material-ui/actions/runs/37929567920), [job](https://github.com/mui/material-ui/actions/runs/37929567920/job/113816673849) (MIT)
- `mui__material-ui__113852813568`: [run](https://github.com/mui/material-ui/actions/runs/37940344037), [job](https://github.com/mui/material-ui/actions/runs/37940344037/job/113852813568) (MIT)
- `mui__material-ui__114017980779`: [run](https://github.com/mui/material-ui/actions/runs/37988971827), [job](https://github.com/mui/material-ui/actions/runs/37988971827/job/114017980779) (MIT)
- `mui__material-ui__114201014183`: [run](https://github.com/mui/material-ui/actions/runs/38047893274), [job](https://github.com/mui/material-ui/actions/runs/38047893274/job/114201014183) (MIT)
- `nestjs__nest__113725957829`: [run](https://github.com/nestjs/nest/actions/runs/37901836927), [job](https://github.com/nestjs/nest/actions/runs/37901836927/job/113725957829) (MIT)
- `nodejs__undici__113454658323`: [run](https://github.com/nodejs/undici/actions/runs/37818935010), [job](https://github.com/nodejs/undici/actions/runs/37818935010/job/113454658323) (MIT)
- `nodejs__undici__113587845596`: [run](https://github.com/nodejs/undici/actions/runs/37858343860), [job](https://github.com/nodejs/undici/actions/runs/37858343860/job/113587845596) (MIT)
- `nodejs__undici__113733370612`: [run](https://github.com/nodejs/undici/actions/runs/37904127267), [job](https://github.com/nodejs/undici/actions/runs/37904127267/job/113733370612) (MIT)
- `nodejs__undici__114444460850`: [run](https://github.com/nodejs/undici/actions/runs/38130771515), [job](https://github.com/nodejs/undici/actions/runs/38130771515/job/114444460850) (MIT)
- `ollama__ollama__110658312118`: [run](https://github.com/ollama/ollama/actions/runs/36949252071), [job](https://github.com/ollama/ollama/actions/runs/36949252071/job/110658312118) (MIT)
- `ollama__ollama__111281811284`: [run](https://github.com/ollama/ollama/actions/runs/37150050686), [job](https://github.com/ollama/ollama/actions/runs/37150050686/job/111281811284) (MIT)
- `ollama__ollama__112050201380`: [run](https://github.com/ollama/ollama/actions/runs/37395431648), [job](https://github.com/ollama/ollama/actions/runs/37395431648/job/112050201380) (MIT)
- `open-telemetry__opentelemetry-collector-contrib__114540400530`: [run](https://github.com/open-telemetry/opentelemetry-collector-contrib/actions/runs/38162595302), [job](https://github.com/open-telemetry/opentelemetry-collector-contrib/actions/runs/38162595302/job/114540400530) (Apache-2.0)
- `open-telemetry__opentelemetry-collector-contrib__114691680706`: [run](https://github.com/open-telemetry/opentelemetry-collector-contrib/actions/runs/38211999823), [job](https://github.com/open-telemetry/opentelemetry-collector-contrib/actions/runs/38211999823/job/114691680706) (Apache-2.0)
- `open-telemetry__opentelemetry-collector-contrib__114696283203`: [run](https://github.com/open-telemetry/opentelemetry-collector-contrib/actions/runs/38214462488), [job](https://github.com/open-telemetry/opentelemetry-collector-contrib/actions/runs/38214462488/job/114696283203) (Apache-2.0)
- `open-telemetry__opentelemetry-collector-contrib__114707267832`: [run](https://github.com/open-telemetry/opentelemetry-collector-contrib/actions/runs/38218028436), [job](https://github.com/open-telemetry/opentelemetry-collector-contrib/actions/runs/38218028436/job/114707267832) (Apache-2.0)
- `open-telemetry__opentelemetry-python__113898003848`: [run](https://github.com/open-telemetry/opentelemetry-python/actions/runs/37953485526), [job](https://github.com/open-telemetry/opentelemetry-python/actions/runs/37953485526/job/113898003848) (Apache-2.0)
- `opensearch-project__OpenSearch__114542165110`: [run](https://github.com/opensearch-project/OpenSearch/actions/runs/38163302349), [job](https://github.com/opensearch-project/OpenSearch/actions/runs/38163302349/job/114542165110) (Apache-2.0)
- `opensearch-project__OpenSearch__114615074145`: [run](https://github.com/opensearch-project/OpenSearch/actions/runs/38188208327), [job](https://github.com/opensearch-project/OpenSearch/actions/runs/38188208327/job/114615074145) (Apache-2.0)
- `opensearch-project__OpenSearch__114698658813`: [run](https://github.com/opensearch-project/OpenSearch/actions/runs/38215239279), [job](https://github.com/opensearch-project/OpenSearch/actions/runs/38215239279/job/114698658813) (Apache-2.0)
- `pnpm__pnpm__114630916551`: [run](https://github.com/pnpm/pnpm/actions/runs/38193444347), [job](https://github.com/pnpm/pnpm/actions/runs/38193444347/job/114630916551) (MIT)
- `pnpm__pnpm__114646745444`: [run](https://github.com/pnpm/pnpm/actions/runs/38198591208), [job](https://github.com/pnpm/pnpm/actions/runs/38198591208/job/114646745444) (MIT)
- `pnpm__pnpm__114647172232`: [run](https://github.com/pnpm/pnpm/actions/runs/38198732514), [job](https://github.com/pnpm/pnpm/actions/runs/38198732514/job/114647172232) (MIT)
- `pola-rs__polars__114486583985`: [run](https://github.com/pola-rs/polars/actions/runs/38145065457), [job](https://github.com/pola-rs/polars/actions/runs/38145065457/job/114486583985) (MIT)
- `pola-rs__polars__114522895855`: [run](https://github.com/pola-rs/polars/actions/runs/38157329937), [job](https://github.com/pola-rs/polars/actions/runs/38157329937/job/114522895855) (MIT)
- `pola-rs__polars__114664980979`: [run](https://github.com/pola-rs/polars/actions/runs/38204536819), [job](https://github.com/pola-rs/polars/actions/runs/38204536819/job/114664980979) (MIT)
- `pola-rs__polars__114710996619`: [run](https://github.com/pola-rs/polars/actions/runs/38219174514), [job](https://github.com/pola-rs/polars/actions/runs/38219174514/job/114710996619) (MIT)
- `pola-rs__polars__114711003282`: [run](https://github.com/pola-rs/polars/actions/runs/38219177347), [job](https://github.com/pola-rs/polars/actions/runs/38219177347/job/114711003282) (MIT)
- `prettier__prettier__114110776414`: [run](https://github.com/prettier/prettier/actions/runs/38017446648), [job](https://github.com/prettier/prettier/actions/runs/38017446648/job/114110776414) (MIT)
- `prettier__prettier__114178983583`: [run](https://github.com/prettier/prettier/actions/runs/38040243909), [job](https://github.com/prettier/prettier/actions/runs/38040243909/job/114178983583) (MIT)
- `prisma__prisma__113732468209`: [run](https://github.com/prisma/orm/actions/runs/37903556602), [job](https://github.com/prisma/orm/actions/runs/37903556602/job/113732468209) (Apache-2.0)
- `prisma__prisma__113919942714`: [run](https://github.com/prisma/orm/actions/runs/37959575922), [job](https://github.com/prisma/orm/actions/runs/37959575922/job/113919942714) (Apache-2.0)
- `prisma__prisma__113920367154`: [run](https://github.com/prisma/orm/actions/runs/37958032000), [job](https://github.com/prisma/orm/actions/runs/37958032000/job/113920367154) (Apache-2.0)
- `prisma__prisma__113980241765`: [run](https://github.com/prisma/orm/actions/runs/37977682224), [job](https://github.com/prisma/orm/actions/runs/37977682224/job/113980241765) (Apache-2.0)
- `prisma__prisma__114173308761`: [run](https://github.com/prisma/orm/actions/runs/38038311957), [job](https://github.com/prisma/orm/actions/runs/38038311957/job/114173308761) (Apache-2.0)
- `prisma__prisma__114651176163`: [run](https://github.com/prisma/orm/actions/runs/38200033863), [job](https://github.com/prisma/orm/actions/runs/38200033863/job/114651176163) (Apache-2.0)
- `prometheus__prometheus__114540001492`: [run](https://github.com/prometheus/prometheus/actions/runs/38163116273), [job](https://github.com/prometheus/prometheus/actions/runs/38163116273/job/114540001492) (Apache-2.0)
- `prometheus__prometheus__114540002085`: [run](https://github.com/prometheus/prometheus/actions/runs/38163116349), [job](https://github.com/prometheus/prometheus/actions/runs/38163116349/job/114540002085) (Apache-2.0)
- `prometheus__prometheus__114690503856`: [run](https://github.com/prometheus/prometheus/actions/runs/38212779790), [job](https://github.com/prometheus/prometheus/actions/runs/38212779790/job/114690503856) (Apache-2.0)
- `pulumi__pulumi__114024391593`: [run](https://github.com/pulumi/pulumi/actions/runs/37989829458), [job](https://github.com/pulumi/pulumi/actions/runs/37989829458/job/114024391593) (Apache-2.0)
- `pulumi__pulumi__114038127102`: [run](https://github.com/pulumi/pulumi/actions/runs/37993759626), [job](https://github.com/pulumi/pulumi/actions/runs/37993759626/job/114038127102) (Apache-2.0)
- `pulumi__pulumi__114513466014`: [run](https://github.com/pulumi/pulumi/actions/runs/38150374442), [job](https://github.com/pulumi/pulumi/actions/runs/38150374442/job/114513466014) (Apache-2.0)
- `pulumi__pulumi__114551319226`: [run](https://github.com/pulumi/pulumi/actions/runs/38166840532), [job](https://github.com/pulumi/pulumi/actions/runs/38166840532/job/114551319226) (Apache-2.0)
- `pulumi__pulumi__114680991169`: [run](https://github.com/pulumi/pulumi/actions/runs/38209170779), [job](https://github.com/pulumi/pulumi/actions/runs/38209170779/job/114680991169) (Apache-2.0)
- `pydantic__pydantic__113900999246`: [run](https://github.com/pydantic/pydantic/actions/runs/37954367941), [job](https://github.com/pydantic/pydantic/actions/runs/37954367941/job/113900999246) (MIT)
- `pydantic__pydantic__114484037956`: [run](https://github.com/pydantic/pydantic/actions/runs/38144202658), [job](https://github.com/pydantic/pydantic/actions/runs/38144202658/job/114484037956) (MIT)
- `pydantic__pydantic__114541587099`: [run](https://github.com/pydantic/pydantic/actions/runs/38163646936), [job](https://github.com/pydantic/pydantic/actions/runs/38163646936/job/114541587099) (MIT)
- `pydantic__pydantic__114655067161`: [run](https://github.com/pydantic/pydantic/actions/runs/38201289690), [job](https://github.com/pydantic/pydantic/actions/runs/38201289690/job/114655067161) (MIT)
- `quarkusio__quarkus__113902287184`: [run](https://github.com/quarkusio/quarkus/actions/runs/37952160621), [job](https://github.com/quarkusio/quarkus/actions/runs/37952160621/job/113902287184) (Apache-2.0)
- `quarkusio__quarkus__114350591017`: [run](https://github.com/quarkusio/quarkus/actions/runs/38098925858), [job](https://github.com/quarkusio/quarkus/actions/runs/38098925858/job/114350591017) (Apache-2.0)
- `storybookjs__storybook__113736895267`: [run](https://github.com/storybookjs/storybook/actions/runs/37905202988), [job](https://github.com/storybookjs/storybook/actions/runs/37905202988/job/113736895267) (MIT)
- `storybookjs__storybook__113828692299`: [run](https://github.com/storybookjs/storybook/actions/runs/37933165774), [job](https://github.com/storybookjs/storybook/actions/runs/37933165774/job/113828692299) (MIT)
- `storybookjs__storybook__114666410443`: [run](https://github.com/storybookjs/storybook/actions/runs/38204995771), [job](https://github.com/storybookjs/storybook/actions/runs/38204995771/job/114666410443) (MIT)
- `supabase__supabase__114714132510`: [run](https://github.com/supabase/supabase/actions/runs/38220141804), [job](https://github.com/supabase/supabase/actions/runs/38220141804/job/114714132510) (Apache-2.0)
- `supabase__supabase__114715996402`: [run](https://github.com/supabase/supabase/actions/runs/38220705078), [job](https://github.com/supabase/supabase/actions/runs/38220705078/job/114715996402) (Apache-2.0)
- `sveltejs__svelte__112744170656`: [run](https://github.com/sveltejs/svelte/actions/runs/37606808024), [job](https://github.com/sveltejs/svelte/actions/runs/37606808024/job/112744170656) (MIT)
- `sveltejs__svelte__112798946537`: [run](https://github.com/sveltejs/svelte/actions/runs/37623383237), [job](https://github.com/sveltejs/svelte/actions/runs/37623383237/job/112798946537) (MIT)
- `sveltejs__svelte__113376198592`: [run](https://github.com/sveltejs/svelte/actions/runs/37796207658), [job](https://github.com/sveltejs/svelte/actions/runs/37796207658/job/113376198592) (MIT)
- `sveltejs__svelte__113985272180`: [run](https://github.com/sveltejs/svelte/actions/runs/37979251934), [job](https://github.com/sveltejs/svelte/actions/runs/37979251934/job/113985272180) (MIT)
- `sveltejs__svelte__114029066815`: [run](https://github.com/sveltejs/svelte/actions/runs/37992224724), [job](https://github.com/sveltejs/svelte/actions/runs/37992224724/job/114029066815) (MIT)
- `sveltejs__svelte__114484764657`: [run](https://github.com/sveltejs/svelte/actions/runs/38144450878), [job](https://github.com/sveltejs/svelte/actions/runs/38144450878/job/114484764657) (MIT)
- `tauri-apps__tauri__114656744137`: [run](https://github.com/tauri-apps/tauri/actions/runs/38201841163), [job](https://github.com/tauri-apps/tauri/actions/runs/38201841163/job/114656744137) (Apache-2.0)
- `tokio-rs__tokio__112995580809`: [run](https://github.com/tokio-rs/tokio/actions/runs/37680674453), [job](https://github.com/tokio-rs/tokio/actions/runs/37680674453/job/112995580809) (MIT)
- `tokio-rs__tokio__113172529999`: [run](https://github.com/tokio-rs/tokio/actions/runs/37734894587), [job](https://github.com/tokio-rs/tokio/actions/runs/37734894587/job/113172529999) (MIT)
- `tokio-rs__tokio__113508169340`: [run](https://github.com/tokio-rs/tokio/actions/runs/37834285347), [job](https://github.com/tokio-rs/tokio/actions/runs/37834285347/job/113508169340) (MIT)
- `tokio-rs__tokio__113919326161`: [run](https://github.com/tokio-rs/tokio/actions/runs/37959532384), [job](https://github.com/tokio-rs/tokio/actions/runs/37959532384/job/113919326161) (MIT)
- `tokio-rs__tokio__114216600948`: [run](https://github.com/tokio-rs/tokio/actions/runs/38053189363), [job](https://github.com/tokio-rs/tokio/actions/runs/38053189363/job/114216600948) (MIT)
- `tokio-rs__tokio__114433571982`: [run](https://github.com/tokio-rs/tokio/actions/runs/38126932312), [job](https://github.com/tokio-rs/tokio/actions/runs/38126932312/job/114433571982) (MIT)
- `tokio-rs__tokio__114456158246`: [run](https://github.com/tokio-rs/tokio/actions/runs/38134725610), [job](https://github.com/tokio-rs/tokio/actions/runs/38134725610/job/114456158246) (MIT)
- `tokio-rs__tokio__114480568779`: [run](https://github.com/tokio-rs/tokio/actions/runs/38143019561), [job](https://github.com/tokio-rs/tokio/actions/runs/38143019561/job/114480568779) (MIT)
- `tokio-rs__tokio__114588495052`: [run](https://github.com/tokio-rs/tokio/actions/runs/38179284528), [job](https://github.com/tokio-rs/tokio/actions/runs/38179284528/job/114588495052) (MIT)
- `traefik__traefik__113339869154`: [run](https://github.com/traefik/traefik/actions/runs/37785735429), [job](https://github.com/traefik/traefik/actions/runs/37785735429/job/113339869154) (MIT)
- `trinodb__trino__114300517085`: [run](https://github.com/trinodb/trino/actions/runs/38081905662), [job](https://github.com/trinodb/trino/actions/runs/38081905662/job/114300517085) (Apache-2.0)
- `trinodb__trino__114390542229`: [run](https://github.com/trinodb/trino/actions/runs/38111904231), [job](https://github.com/trinodb/trino/actions/runs/38111904231/job/114390542229) (Apache-2.0)
- `trinodb__trino__114579657282`: [run](https://github.com/trinodb/trino/actions/runs/38176418752), [job](https://github.com/trinodb/trino/actions/runs/38176418752/job/114579657282) (Apache-2.0)
- `trinodb__trino__114648262856`: [run](https://github.com/trinodb/trino/actions/runs/38199099077), [job](https://github.com/trinodb/trino/actions/runs/38199099077/job/114648262856) (Apache-2.0)
- `typescript-eslint__typescript-eslint__112223516113`: [run](https://github.com/typescript-eslint/typescript-eslint/actions/runs/37449583641), [job](https://github.com/typescript-eslint/typescript-eslint/actions/runs/37449583641/job/112223516113) (MIT)
- `typescript-eslint__typescript-eslint__112784126696`: [run](https://github.com/typescript-eslint/typescript-eslint/actions/runs/37618785957), [job](https://github.com/typescript-eslint/typescript-eslint/actions/runs/37618785957/job/112784126696) (MIT)
- `typescript-eslint__typescript-eslint__114236057035`: [run](https://github.com/typescript-eslint/typescript-eslint/actions/runs/38059907923), [job](https://github.com/typescript-eslint/typescript-eslint/actions/runs/38059907923/job/114236057035) (MIT)
- `typescript-eslint__typescript-eslint__114426314888`: [run](https://github.com/typescript-eslint/typescript-eslint/actions/runs/38124573123), [job](https://github.com/typescript-eslint/typescript-eslint/actions/runs/38124573123/job/114426314888) (MIT)
- `typescript-eslint__typescript-eslint__114508797415`: [run](https://github.com/typescript-eslint/typescript-eslint/actions/runs/38152446056), [job](https://github.com/typescript-eslint/typescript-eslint/actions/runs/38152446056/job/114508797415) (MIT)
- `vercel__next.js__114247779668`: [run](https://github.com/vercel/next.js/actions/runs/38063981091), [job](https://github.com/vercel/next.js/actions/runs/38063981091/job/114247779668) (MIT)
- `vercel__next.js__114255054247`: [run](https://github.com/vercel/next.js/actions/runs/38066184725), [job](https://github.com/vercel/next.js/actions/runs/38066184725/job/114255054247) (MIT)
- `vercel__next.js__114612679301`: [run](https://github.com/vercel/next.js/actions/runs/38187342058), [job](https://github.com/vercel/next.js/actions/runs/38187342058/job/114612679301) (MIT)
- `vercel__next.js__114697443308`: [run](https://github.com/vercel/next.js/actions/runs/38214550248), [job](https://github.com/vercel/next.js/actions/runs/38214550248/job/114697443308) (MIT)
- `vercel__next.js__114706175837`: [run](https://github.com/vercel/next.js/actions/runs/38217690831), [job](https://github.com/vercel/next.js/actions/runs/38217690831/job/114706175837) (MIT)
- `vitejs__vite__114009293942`: [run](https://github.com/vitejs/vite/actions/runs/37986166856), [job](https://github.com/vitejs/vite/actions/runs/37986166856/job/114009293942) (MIT)
- `vitejs__vite__114630824045`: [run](https://github.com/vitejs/vite/actions/runs/38193411344), [job](https://github.com/vitejs/vite/actions/runs/38193411344/job/114630824045) (MIT)
- `vitejs__vite__114695745519`: [run](https://github.com/vitejs/vite/actions/runs/38214414602), [job](https://github.com/vitejs/vite/actions/runs/38214414602/job/114695745519) (MIT)
- `vitejs__vite__114708776239`: [run](https://github.com/vitejs/vite/actions/runs/38218454942), [job](https://github.com/vitejs/vite/actions/runs/38218454942/job/114708776239) (MIT)
- `vitest-dev__vitest__112220496972`: [run](https://github.com/vitest-dev/vitest/actions/runs/37448888269), [job](https://github.com/vitest-dev/vitest/actions/runs/37448888269/job/112220496972) (MIT)
- `vitest-dev__vitest__112411213380`: [run](https://github.com/vitest-dev/vitest/actions/runs/37504947722), [job](https://github.com/vitest-dev/vitest/actions/runs/37504947722/job/112411213380) (MIT)
- `vitest-dev__vitest__114676475998`: [run](https://github.com/vitest-dev/vitest/actions/runs/38208264269), [job](https://github.com/vitest-dev/vitest/actions/runs/38208264269/job/114676475998) (MIT)
- `vllm-project__vllm__114704015294`: [run](https://github.com/vllm-project/vllm/actions/runs/38217006217), [job](https://github.com/vllm-project/vllm/actions/runs/38217006217/job/114704015294) (Apache-2.0)
- `vllm-project__vllm__114715538081`: [run](https://github.com/vllm-project/vllm/actions/runs/38220569076), [job](https://github.com/vllm-project/vllm/actions/runs/38220569076/job/114715538081) (Apache-2.0)
- `vllm-project__vllm__114719091009`: [run](https://github.com/vllm-project/vllm/actions/runs/38221653090), [job](https://github.com/vllm-project/vllm/actions/runs/38221653090/job/114719091009) (Apache-2.0)
- `vuejs__core__113328260108`: [run](https://github.com/vuejs/core/actions/runs/37782327802), [job](https://github.com/vuejs/core/actions/runs/37782327802/job/113328260108) (MIT)
- `vuejs__core__114636213911`: [run](https://github.com/vuejs/core/actions/runs/38195203451), [job](https://github.com/vuejs/core/actions/runs/38195203451/job/114636213911) (MIT)
- `vuejs__core__114699779903`: [run](https://github.com/vuejs/core/actions/runs/38215695932), [job](https://github.com/vuejs/core/actions/runs/38215695932/job/114699779903) (MIT)
