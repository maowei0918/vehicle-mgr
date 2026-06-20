from pathlib import Path
base=Path('/vol1/@appshare/com.dustinky.qwenpaw/.qwenpaw/workspaces/default/XiaomiAlbumSyncer-Acckion')
# ArchiveRecord enum
p=base/'server/src/main/kotlin/com/coooolfan/xiaomialbumsyncer/model/ArchiveRecord.kt'
s=p.read_text()
if 'enum class ArchiveSource' not in s:
    s=s.replace('''enum class ArchiveMode {
    DISABLED,
    TIME,
    SPACE
}

// 归档状态枚举''','''enum class ArchiveMode {
    DISABLED,
    TIME,
    SPACE
}

// 归档源枚举
// LOCAL: 从本地同步文件夹复制到归档文件夹
// CLOUD: 从云端重新下载到归档文件夹
enum class ArchiveSource {
    LOCAL,
    CLOUD
}

// 归档状态枚举''')
    p.write_text(s)
# CrontabConfig
p=base/'server/src/main/kotlin/com/coooolfan/xiaomialbumsyncer/model/CrontabConfig.kt'
s=p.read_text()
if 'archiveSource' not in s:
    s=s.replace('''    val backupFolder: String = "backup",            // 归档文件夹名称（相对于 targetPath）
    val deleteCloudAfterArchive: Boolean = true,    // 归档后是否删除云端

    val notify: Boolean = true,''','''    val backupFolder: String = "backup",            // 归档文件夹名称（相对于 targetPath）
    val archiveSource: ArchiveSource = ArchiveSource.LOCAL, // 归档源：LOCAL 从本地复制，CLOUD 从云端重新下载
    val deleteCloudAfterArchive: Boolean = true,    // 兼容旧配置；新归档逻辑归档成功后总是删除云端

    val notify: Boolean = true,''')
    p.write_text(s)
