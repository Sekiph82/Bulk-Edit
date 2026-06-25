# Media Library

## Storage

All media stored in S3-compatible object storage (MinIO local, AWS S3 or Cloudflare R2 in production).

Media files are NEVER stored on application servers.

## Upload Flow

```
1. Frontend calls POST /media/upload-url with { filename, content_type }
2. Backend generates S3 presigned PUT URL (expires in 15 minutes)
3. Backend returns { upload_url, s3_key, media_asset_id }
4. Frontend uploads directly to S3 via presigned URL
5. Frontend calls POST /media to save metadata
6. Backend stores MediaAsset row in DB
```

## S3 Key Structure

```
{organization_id}/{YYYY}/{MM}/{uuid}.{ext}
```

Example: `org-123/2026/06/media-uuid.jpg`

## Supported File Types

| Type | Extensions | Max Size |
|---|---|---|
| Image | jpg, jpeg, png, gif, webp | 25 MB |
| Video | mp4, mov | 100 MB |

## Validation

Validated before generating presigned URL:
- File extension in whitelist
- Content-Type matches extension
- File size within plan limit

## Thumbnail Generation

For images: generate 570px-wide thumbnail after upload via Celery task.
Store thumbnail S3 key in `media_assets.thumbnail_s3_key`.

## Serving Media

Media is served directly from S3/CDN. Backend never proxies media files.

## Deletion

On `DELETE /media/{id}`:
1. Delete S3 object
2. Delete `media_assets` row
3. Remove references from any listings (set to null)
