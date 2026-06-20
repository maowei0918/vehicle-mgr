from pathlib import Path
p=Path('/vol1/@appshare/com.dustinky.qwenpaw/.qwenpaw/workspaces/default/XiaomiAlbumSyncer-Acckion/server/src/main/kotlin/com/coooolfan/xiaomialbumsyncer/service/ArchiveService.kt')
s=p.read_text()
s=s.replace('''            updateArchiveStatus(archiveRecord.id, ArchiveStatus.MOVING_FILES, null)
            plan.assetsToArchive.forEach { asset ->
                try {
                    val detail = moveToBackup(asset, syncFolder, backupFolder)
                    recordArchiveDetail(archiveRecord.id, detail)
                } catch (e: Exception) {
                    log.error("移动文件到 backup 失败: ${asset.fileName}", e)
                    recordArchiveDetail(
                        archiveRecord.id,
                        ArchiveDetail {
                            this.archiveRecordId = archiveRecord.id
                            this.assetId = asset.id
                            sourcePath = Path(syncFolder.toString(), asset.album.name, asset.fileName).toString()
                            targetPath = Path(backupFolder.toString(), asset.album.name, asset.fileName).toString()
                            isMovedToBackup = false
                            isDeletedFromCloud = false
                            errorMessage = e.message
                        }
                    )
                }
            }

            if (config.deleteCloudAfterArchive) {
                updateArchiveStatus(archiveRecord.id, ArchiveStatus.DELETING_CLOUD, null)

                val successfullyMovedAssetIds = getSuccessfullyMovedAssetIds(archiveRecord.id)

                if (successfullyMovedAssetIds.isNotEmpty()) {
                    val deletedIds = xiaoMiApi.batchDeleteAssets(crontab.accountId, successfullyMovedAssetIds)

                    deletedIds.forEach { assetId ->
                        updateArchiveDetailCloudDeleted(archiveRecord.id, assetId)
                    }
                }
            }
''','''            updateArchiveStatus(archiveRecord.id, ArchiveStatus.MOVING_FILES, null)
            plan.assetsToArchive.forEach { asset ->
                try {
                    val detail = archiveToBackup(
                        asset = asset,
                        syncFolder = syncFolder,
                        backupFolder = backupFolder,
                        archiveSource = config.archiveSource,
                        accountId = crontab.accountId
                    )
                    recordArchiveDetail(archiveRecord.id, detail)
                } catch (e: Exception) {
                    log.error("归档文件到 backup 失败: ${asset.fileName}, source=${config.archiveSource}", e)
                    recordArchiveDetail(
                        archiveRecord.id,
                        ArchiveDetail {
                            this.archiveRecordId = archiveRecord.id
                            this.assetId = asset.id
                            sourcePath = archiveSourcePath(asset, syncFolder, config.archiveSource)
                            targetPath = Path(backupFolder.toString(), asset.album.name, asset.fileName).toString()
                            isMovedToBackup = false
                            isDeletedFromCloud = false
                            errorMessage = e.message
                        }
                    )
                }
            }

            updateArchiveStatus(archiveRecord.id, ArchiveStatus.DELETING_CLOUD, null)

            val successfullyArchivedAssetIds = getSuccessfullyMovedAssetIds(archiveRecord.id)

            if (successfullyArchivedAssetIds.isNotEmpty()) {
                val deletedIds = xiaoMiApi.batchDeleteAssets(crontab.accountId, successfullyArchivedAssetIds)

                deletedIds.forEach { assetId ->
                    updateArchiveDetailCloudDeleted(archiveRecord.id, assetId)
                }
            }
''')
start=s.index('    private fun moveToBackup(')
end=s.index('    private fun createArchiveRecord', start)
new='''    private fun archiveToBackup(
        asset: Asset,
        syncFolder: Path,
        backupFolder: Path,
        archiveSource: ArchiveSource,
        accountId: Long
    ): ArchiveDetail {
        return when (archiveSource) {
            ArchiveSource.LOCAL -> copyLocalToBackup(asset, syncFolder, backupFolder)
            ArchiveSource.CLOUD -> downloadCloudToBackup(asset, backupFolder, accountId)
        }
    }

    private fun archiveSourcePath(asset: Asset, syncFolder: Path, archiveSource: ArchiveSource): String {
        return when (archiveSource) {
            ArchiveSource.LOCAL -> Path(syncFolder.toString(), asset.album.name, asset.fileName).toString()
            ArchiveSource.CLOUD -> "cloud://${asset.id}/${asset.fileName}"
        }
    }

    private fun copyLocalToBackup(asset: Asset, syncFolder: Path, backupFolder: Path): ArchiveDetail {
        val sourcePath = Path(syncFolder.toString(), asset.album.name, asset.fileName)
        val targetPath = Path(backupFolder.toString(), asset.album.name, asset.fileName)

        if (targetPath.exists()) {
            val isValid = fileService.verifySha1(targetPath, asset.sha1)
            if (isValid) {
                updateBackupFileTime(asset, targetPath)
                return archiveDetail(asset, sourcePath.toString(), targetPath.toString(), "文件已存在于 backup 文件夹")
            }
            throw FileIntegrityException("backup 文件夹中的文件完整性验证失败：${asset.fileName}")
        }

        if (!sourcePath.exists()) {
            throw IOException("本地同步文件不存在，无法从本地归档: ${asset.fileName}")
        }

        fileService.copyFile(sourcePath, targetPath)
        val isValid = fileService.verifySha1(targetPath, asset.sha1)

        if (!isValid) {
            try {
                fileService.deleteFile(targetPath)
            } catch (e: Exception) {
                log.warn("删除完整性验证失败的归档文件失败: $targetPath", e)
            }
            throw FileIntegrityException("文件完整性验证失败：${asset.fileName}")
        }

        updateBackupFileTime(asset, targetPath)
        return archiveDetail(asset, sourcePath.toString(), targetPath.toString(), null)
    }

    private fun downloadCloudToBackup(asset: Asset, backupFolder: Path, accountId: Long): ArchiveDetail {
        val sourcePath = "cloud://${asset.id}/${asset.fileName}"
        val targetPath = Path(backupFolder.toString(), asset.album.name, asset.fileName)

        if (targetPath.exists()) {
            val isValid = fileService.verifySha1(targetPath, asset.sha1)
            if (isValid) {
                updateBackupFileTime(asset, targetPath)
                return archiveDetail(asset, sourcePath, targetPath.toString(), "文件已存在于 backup 文件夹")
            }
            throw FileIntegrityException("backup 文件夹中的文件完整性验证失败：${asset.fileName}")
        }

        val downloadedPath = xiaoMiApi.downloadAsset(accountId, asset, targetPath)
        if (downloadedPath.toString() == "/tmp/DELETED") {
            throw IOException("云端文件已不存在，无法从云端归档: ${asset.fileName}")
        }

        val isValid = fileService.verifySha1(targetPath, asset.sha1)
        if (!isValid) {
            try {
                fileService.deleteFile(targetPath)
            } catch (e: Exception) {
                log.warn("删除完整性验证失败的云端归档文件失败: $targetPath", e)
            }
            throw FileIntegrityException("云端下载文件完整性验证失败：${asset.fileName}")
        }

        updateBackupFileTime(asset, targetPath)
        return archiveDetail(asset, sourcePath, targetPath.toString(), null)
    }

    private fun updateBackupFileTime(asset: Asset, targetPath: Path) {
        try {
            fileTimeStage.updateFileSystemTime(asset, targetPath)
        } catch (e: Exception) {
            log.warn("更新归档文件的文件系统时间失败: ${asset.fileName}", e)
        }
    }

    private fun archiveDetail(asset: Asset, sourcePath: String, targetPath: String, errorMessage: String?): ArchiveDetail {
        return ArchiveDetail {
            this.assetId = asset.id
            this.sourcePath = sourcePath
            this.targetPath = targetPath
            this.isMovedToBackup = true
            this.isDeletedFromCloud = false
            this.errorMessage = errorMessage
        }
    }

'''
s=s[:start]+new+s[end:]
p.write_text(s)
