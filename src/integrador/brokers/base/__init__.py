import logging
import rule_engine
from coorte.models import Cohort


logger = logging.getLogger(__name__)


class BaseBroker:

    def __init__(self, solicitacao):
        self.solicitacao = solicitacao

    @property
    def credentials(self) -> dict:
        c = {"Authentication": f"Token {self.solicitacao.ambiente.token}"}
        return c

    def cast_cohort(self, c: Cohort) -> dict:
        return {
            "nome": c.name,
            "role": c.papel.papel,
            "ativo": c.active,
            "idnumber": c.idnumber,
            "descricao": c.description,
            "colaboradores": [
                {
                    "nome": e.colaborador.get_full_name(),
                    "email": e.colaborador.email,
                    "login": e.colaborador.username,
                    "status": e.colaborador.is_active
                }
                for e in c.enrolments.all()
            ]
        }
    def cohort_matches(self, cohort: Cohort, rule_field: str) -> dict:
        try:
            return rule_engine.Rule(getattr(cohort, rule_field)).matches(self.solicitacao.recebido)
        except Exception as e:
            logger.warning(f"Erro ao avaliar a regra do cohort {cohort.id} ({cohort.name}): {e}")
            return False

    def get_cohort(self) -> list:



        all_cohort = Cohort.objects.filter(active=True)
        cohort_eligiveis = (
            [self.cast_cohort(c) for c in all_cohort if self.cohort_matches(c, "rule_diario")] 
            +
            [self.cast_cohort(c) for c in all_cohort if self.cohort_matches(c, "rule_coordenacao")]
        )
        return cohort_eligiveis

    def sync_up_enrolments(self) -> dict:
        raise NotImplementedError("Este método deve ser implementado pelas subclasses.")

    def sync_down_grades(self) -> dict:
        raise NotImplementedError("Este método deve ser implementado pelas subclasses.")
