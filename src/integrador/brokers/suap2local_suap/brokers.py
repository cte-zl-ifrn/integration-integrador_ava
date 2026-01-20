import logging
from edu.models import Curso, Polo, Programa
from coorte.models import Coorte, dados_vinculo
from integrador.models import Solicitacao
from integrador.utils import SyncError, get_json_api, post_json_api


logger = logging.getLogger(__name__)


class Suap2LocalSuapBroker:

    def __get_coortes(self) -> list:
        coortes = []
        try:
            curso, created = Curso.objects.get_or_create(
                suap_id=recebido["curso"]["id"],
                codigo=recebido["curso"]["codigo"],
                nome=recebido["curso"]["nome"],
                descricao=recebido["curso"]["descricao"],
            )
            if created:
                print(f"O curso foi criado {curso.nome}")
            else:
                coortes += Coorte.objects.filter(coortecurso__curso=curso)
        except:
            pass

        try:
            programas_set = set([a.get("programa") for a in recebido.get("alunos", [])])
            for p in programas_set:
                programa, created = Programa.objects.get_or_create(sigla=p, nome=p)
                if created:
                    print(f"O programa foi criado {programa.sigla}")
                else:
                    coortes += Coorte.objects.filter(coorteprograma__programa=programa)
        except:
            pass

        try:
            polos_set = set([a.get("polo", {}).get("descricao") for a in recebido.get("alunos", [])])
            for p in Polo.objects.filter(nome__in=polos_set):
                coortes += Coorte.objects.filter(coortepolo__polo=p)
        except:
            pass

        objects_list = [
            {
                "idnumber": coo.papel.sigla,
                "nome": coo.papel.nome,
                "ativo": coo.papel.active,
                "role": coo.papel.papel,
                "descricao": coo.papel.nome,
                "colaboradores": (
                    [dados_vinculo(vinc) for vinc in coo.vinculos.all()] if hasattr(coo, "vinculos") else None
                ),
            }
            for coo in coortes
        ]

        return list(objects_list)

    def enviar_diarios(self, solicitacao: Solicitacao) -> dict:
        try:
            solicitacao.enviado = dict(**solicitacao.recebido, **{"coortes": self.__get_coortes()})
            solicitacao.save()
        except Exception as e:
            SyncError(f"Erro ao tentar obter as coortes antes de iniciar a integração com o AVA. Contacte um administrador. Erro: {e}.", getattr(e, "code", 525))

        return post_json_api(solicitacao.ambiente, 'sync_up_enrolments', solicitacao.enviado)

    def baixar_notas(self, solicitacao: Solicitacao) -> dict:
        return get_json_api(solicitacao.ambiente, "sync_down_grades", diario_id=solicitacao.diario_id)
