from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Router, Schema

from django.contrib.admin.views.decorators import staff_member_required
from integrador.suap2local_suap.brokers import Suap2LocalSuapBroker


class SincronizacaoIn(Schema):
    pass


class SincronizacaoOut(Schema):
    pass


class NotasOut(Schema):
    pass


# api = NinjaAPI(docs_decorator=staff_member_required)
router = Router()


@router.path('/suap')
class Suap2LocalSuapApi:
    def __init__(self, request):
        # user_projects = request.user.project_set
        # self.project = get_object_or_404(user_projects, id=project_id))
        # self.tasks = self.project.task_set.all()
        self.broker = Suap2LocalSuapBroker()

    @router.get('/enviar_diarios/', response=SincronizacaoOut)
    def enviar_diarios(self, request) -> SincronizacaoOut:
        request.solicitacao
        return SincronizacaoOut(self.broker.enviar_diarios())

    @router.get('/baixar_notas/', response=NotasOut)
    def baixar_notas(self, request) -> NotasOut:
        return NotasOut(self.broker.baixar_notas())

api = NinjaAPI()
