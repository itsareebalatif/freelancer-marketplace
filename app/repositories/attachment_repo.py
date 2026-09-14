from app.models.attachment import Attachment
from app.models.enums import AttachmentResourceType
from app.repositories.base import BaseRepository


class AttachmentRepository(BaseRepository):
    def get_by_id(self, attachment_id) -> Attachment | None:
        return self.db.query(Attachment).filter(Attachment.id == attachment_id).first()

    def get_by_checksum(self, resource_type: AttachmentResourceType, resource_id, checksum: str) -> Attachment | None:
        return (
            self.db.query(Attachment)
            .filter(
                Attachment.resource_type == resource_type,
                Attachment.resource_id == resource_id,
                Attachment.checksum == checksum,
            )
            .first()
        )

    def list_for_resource(self, resource_type: AttachmentResourceType, resource_id) -> list[Attachment]:
        return (
            self.db.query(Attachment)
            .filter(Attachment.resource_type == resource_type, Attachment.resource_id == resource_id)
            .order_by(Attachment.created_at.desc())
            .all()
        )

    def create(self, **fields) -> Attachment:
        attachment = Attachment(**fields)
        return self.add(attachment)

    def delete(self, attachment: Attachment) -> None:
        self.db.delete(attachment)
        self.db.commit()
