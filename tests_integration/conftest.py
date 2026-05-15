import os
import subprocess
import time

import pytest
import sc4net

from integrador.models import Ambiente

MOODLE_URL = os.getenv("MOODLE_INTEGRATION_URL", "http://localhost:8080")


def wait_for_url(url, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # sc4net.get retorna o conteúdo decodificado por padrão
            sc4net.get(url, timeout=2)
            return True
        except Exception:
            pass
        time.sleep(2)
    return False


@pytest.fixture(scope="session", autouse=True)
def docker_compose():
    """Garante que o ambiente Docker está rodando se estivermos fora dele."""
    # Se estivermos rodando via docker-compose (integrador-integration),
    # não precisamos subir o docker novamente.
    if os.getenv("MOODLE_INTEGRATION_URL"):
        print("\nRodando dentro do Docker, pulando docker compose up.")
        if not wait_for_url(MOODLE_URL):
            pytest.fail(f"Moodle em {MOODLE_URL} não ficou pronto a tempo.")
        yield
        return

    print("\nSubindo ambiente Docker para integração...")
    # Tenta docker compose (v2) depois docker-compose (v1)
    try:
        subprocess.run(["docker", "compose", "-f", "docker-compose.integration.yml", "up", "-d", "--wait"], check=True)
    except Exception:
        subprocess.run(["docker-compose", "-f", "docker-compose.integration.yml", "up", "-d"], check=True)

    if not wait_for_url(MOODLE_URL):
        pytest.fail(f"Moodle em {MOODLE_URL} não ficou pronto a tempo.")

    yield


@pytest.fixture(scope="session")
def moodle_seed_data(docker_compose):
    """Executa o seed de dados no Moodle e retorna os IDs criados."""
    print("Executando seed no Moodle...")

    # Tentamos encontrar o ID do container do moodle.
    try:
        # Tenta pelo label do compose (mais robusto, filtrando pelo projeto)
        # O nome do projeto por padrão é o nome da pasta (integrador_ava)
        container_id = (
            subprocess.check_output(
                [
                    "docker",
                    "ps",
                    "-q",
                    "--filter",
                    "label=com.docker.compose.service=moodle",
                    "--filter",
                    "label=com.docker.compose.project=integrador_ava",
                    "--filter",
                    "status=running",
                ]
            )
            .decode()
            .strip()
            .split("\n")[0]
        )

        if not container_id:
            # Fallback para nome
            container_id = (
                subprocess.check_output(["docker", "ps", "-q", "--filter", "name=moodle", "--filter", "status=running"])
                .decode()
                .strip()
                .split("\n")[0]
            )

        if not container_id:
            pytest.fail("Não foi possível encontrar o ID do container do Moodle.")

        subprocess.run(["docker", "exec", container_id, "php", "/var/www/html/scripts/seed_moodle.php"], check=True)

        # Silencia warnings/notices no Moodle para não sujar o JSON
        subprocess.run(
            [
                "docker",
                "exec",
                container_id,
                "bash",
                "-c",
                "sed -i 's/ini_set(.display_errors., 1)/ini_set(\"display_errors\", 0)/g' /var/www/html/local/suap/api/index.php",
            ],
            check=True,
        )
        subprocess.run(
            [
                "docker",
                "exec",
                container_id,
                "bash",
                "-c",
                "sed -i 's/error_reporting(E_ALL)/error_reporting(0)/g' /var/www/html/local/suap/api/index.php",
            ],
            check=True,
        )

        # Corrige bug no sync_down_grades.php (json_decode em algo que já pode ser array/object no PG)
        subprocess.run(
            [
                "docker",
                "exec",
                container_id,
                "bash",
                "-c",
                r"sed -i 's/jsonb_object_agg(gi.idnumber::text, gg.finalgrade)/jsonb_object_agg(gi.idnumber::text, gg.finalgrade)::text/g' /var/www/html/local/suap/api/sync_down_grades.php",
            ],
            check=True,
        )
        subprocess.run(
            [
                "docker",
                "exec",
                container_id,
                "bash",
                "-c",
                r"sed -i 's/json_decode(\$aluno->notas)/is_string(\$aluno->notas) ? json_decode(\$aluno->notas) : \$aluno->notas/g' /var/www/html/local/suap/api/sync_down_grades.php",
            ],
            check=True,
        )

        # Lê o arquivo de seed_data.json criado no container
        # Como o volume está montado, podemos ler direto do host
        seed_file = os.path.join(os.path.dirname(__file__), "scripts", "seed_data.json")
        import json

        with open(seed_file, "r") as f:
            data = json.load(f)

        print(f"Seed e ajustes finalizados com sucesso. Data: {data}")
        return data
    except Exception as e:
        print(f"Erro ao tentar executar o seed: {e}")
        if not os.getenv("IGNORE_SEED_FAILURE"):
            raise


@pytest.fixture
def integration_ambiente(db, moodle_seed_data):
    """Cria o ambiente no Django apontando para o Moodle Docker."""

    ambiente, created = Ambiente.objects.update_or_create(
        nome="Moodle Local Docker",
        defaults={
            "url": MOODLE_URL,
            "expressao_seletora": "campus.sigla == 'ZL'",
            "local_suap_token": "test_token",
            "local_suap_active": True,
            "ordem": 0,
        },
    )
    return ambiente
