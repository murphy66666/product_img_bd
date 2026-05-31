from app.schemas.template import SmartTemplate, SmartTemplateType
from app.services.repository import repository


class TemplateService:
    async def list_templates(self, template_type: SmartTemplateType | None = None) -> list[SmartTemplate]:
        return await repository.list_smart_templates(template_type)


def get_template_service() -> TemplateService:
    return TemplateService()
