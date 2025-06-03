from locust import HttpUser, TaskSet, task, between
import json

incrementador = 0


class EnviarDiariosTaskSet(TaskSet):
    @task
    def enviar_diarios(self):
        global incrementador
        with open("integrador/example/data.json", "r") as file:
            incrementador += 1
            solicitaca = json.load(file)
            solicitaca["turma"]["codigo"] = f"20251.1.15312.555.{incrementador}E"
            self.client.post(
                "/api/enviar_diarios/",
                json=solicitaca,
                headers={"Authentication": "Token changeme"},
            )


class EnviarDiariosUser(HttpUser):
    tasks = [EnviarDiariosTaskSet]
    wait_time = between(1, 3)


if __name__ == "__main__":
    import os

    os.system("locust -f locust.py --host=http://integrador --users 300 --spawn-rate 50")
