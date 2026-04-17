-- Repair Album-Asset Relations
-- Dieses Skript verknüpft Assets mit den passenden Alben basierend auf der Ordnerstruktur.

-- Schritt 1: Verknüpfe Assets aus /imported/<AlbumName>/... mit dem passenden Album
INSERT INTO album_asset ("albumId", "assetId", "createdAt")
SELECT DISTINCT
    alb.id AS "albumId",
    ast.id AS "assetId",
    NOW() AS "createdAt"
FROM asset ast
JOIN album alb ON alb."deletedAt" IS NULL
    AND alb."albumName" = regexp_replace(ast."originalPath", '^/imported/([^/]+)/.*$', '\1')
WHERE ast."originalPath" LIKE '/imported/%'
  AND ast."originalPath" NOT LIKE '/imported/recovered_takeout_2026/%'
  AND ast."deletedAt" IS NULL
ON CONFLICT DO NOTHING;

-- Schritt 2: Verknüpfe Assets aus /imported/recovered_takeout_2026/Takeout/Google Photos/<AlbumName>/...
INSERT INTO album_asset ("albumId", "assetId", "createdAt")
SELECT DISTINCT
    alb.id AS "albumId",
    ast.id AS "assetId",
    NOW() AS "createdAt"
FROM asset ast
JOIN album alb ON alb."deletedAt" IS NULL
    AND alb."albumName" = regexp_replace(ast."originalPath", '^/imported/recovered_takeout_2026/Takeout/Google Photos/([^/]+)/.*$', '\1')
WHERE ast."originalPath" LIKE '/imported/recovered_takeout_2026/Takeout/Google Photos/%'
  AND ast."deletedAt" IS NULL
ON CONFLICT DO NOTHING;

-- Schritt 3: Setze Thumbnail-Asset für jedes Album (erstes Bild im Album)
UPDATE album
SET "albumThumbnailAssetId" = sub."assetId"
FROM (
    SELECT DISTINCT ON (aa."albumId") aa."albumId", aa."assetId"
    FROM album_asset aa
    JOIN asset a ON a.id = aa."assetId" AND a.type = 'IMAGE'
    ORDER BY aa."albumId", aa."createdAt"
) sub
WHERE album.id = sub."albumId"
  AND album."albumThumbnailAssetId" IS NULL;
