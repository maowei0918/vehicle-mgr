from pathlib import Path
base=Path('/vol1/@appshare/com.dustinky.qwenpaw/.qwenpaw/workspaces/default/XiaomiAlbumSyncer-Acckion/web/src')
# enum file
p=base/'__generated/model/enums/ArchiveSource.ts'
if not p.exists():
    p.write_text("""export type ArchiveSource = 'LOCAL' | 'CLOUD';\n\nexport const ArchiveSource_CONSTANTS: ArchiveSource[] = [\n    'LOCAL', \n    'CLOUD'\n];\n""")
# enum index
p=base/'__generated/model/enums/index.ts'
s=p.read_text()
if "ArchiveSource" not in s:
    s=s.replace("export type {ArchiveStatus} from './ArchiveStatus';\nexport {ArchiveStatus_CONSTANTS} from './ArchiveStatus';", "export type {ArchiveStatus} from './ArchiveStatus';\nexport {ArchiveStatus_CONSTANTS} from './ArchiveStatus';\nexport type {ArchiveSource} from './ArchiveSource';\nexport {ArchiveSource_CONSTANTS} from './ArchiveSource';")
    p.write_text(s)
# static config import/field
p=base/'__generated/model/static/CrontabConfig.ts'
s=p.read_text()
s=s.replace("import type {ArchiveMode, SyncMode} from '../enums/';", "import type {ArchiveMode, ArchiveSource, SyncMode} from '../enums/';")
if 'readonly archiveSource' not in s:
    s=s.replace("    readonly backupFolder: string;\n    readonly deleteCloudAfterArchive: boolean;", "    readonly backupFolder: string;\n    readonly archiveSource: ArchiveSource;\n    readonly deleteCloudAfterArchive: boolean;")
p.write_text(s)
# default/map form
p=base/'utils/crontabForm.ts'
s=p.read_text()
if "archiveSource: 'LOCAL'" not in s:
    s=s.replace("    backupFolder: 'backup',\n    deleteCloudAfterArchive: true,", "    backupFolder: 'backup',\n    archiveSource: 'LOCAL',\n    deleteCloudAfterArchive: true,")
    s=s.replace("      backupFolder: item.config.backupFolder ?? 'backup',\n      deleteCloudAfterArchive: item.config.deleteCloudAfterArchive ?? true,", "      backupFolder: item.config.backupFolder ?? 'backup',\n      archiveSource: item.config.archiveSource ?? 'LOCAL',\n      deleteCloudAfterArchive: item.config.deleteCloudAfterArchive ?? true,")
    p.write_text(s)
# UI insert options and block
p=base/'components/CronFormDialog.vue'
s=p.read_text()
if 'archiveSourceOptions' not in s:
    insert="""
const archiveSourceOptions = [
  { label: '本地', value: 'LOCAL', description: '从本地同步文件夹复制到归档文件夹，原本地文件保留' },
  { label: '云端', value: 'CLOUD', description: '从小米云端重新下载源文件到归档文件夹' },
]
"""
    s=s.replace("const timeZones = computed(() => [...props.timeZones])\n", "const timeZones = computed(() => [...props.timeZones])\n"+insert)
if '归档源' not in s:
    block="""\n              <div class=\"space-y-2\">\n                <label class=\"block text-xs font-medium text-slate-500\">归档源</label>\n                <Select\n                  v-model=\"form.config.archiveSource\"\n                  :options=\"archiveSourceOptions\"\n                  option-label=\"label\"\n                  option-value=\"value\"\n                  class=\"w-full\"\n                />\n                <div class=\"text-[10px] text-slate-400\">\n                  {{ archiveSourceOptions.find((item) => item.value === form.config.archiveSource)?.description }}\n                </div>\n              </div>\n"""
    s=s.replace("""              <div class=\"space-y-2\">\n                <label class=\"block text-xs font-medium text-slate-500\">归档文件夹名称</label>\n                <InputText v-model=\"form.config.backupFolder\" placeholder=\"backup\" class=\"w-full\" />\n                <div class=\"text-[10px] text-slate-400\">\n                  相对于保存路径的文件夹名称，用于存放归档的照片\n                </div>\n              </div>\n""", """              <div class=\"space-y-2\">\n                <label class=\"block text-xs font-medium text-slate-500\">归档文件夹名称</label>\n                <InputText v-model=\"form.config.backupFolder\" placeholder=\"backup\" class=\"w-full\" />\n                <div class=\"text-[10px] text-slate-400\">\n                  相对于保存路径的文件夹名称，用于存放归档的照片\n                </div>\n              </div>\n"""+block)
# adjust deletion warning text: always deletes cloud
s=s.replace("""                  <ToggleSwitch v-model=\"form.config.deleteCloudAfterArchive\" />\n                  <span>归档后删除云端</span>\n""", """                  <ToggleSwitch v-model=\"form.config.deleteCloudAfterArchive\" disabled />\n                  <span>归档成功后删除云端</span>\n""")
s=s.replace("警告：启用此选项后，归档的照片将从小米云端永久删除，请确保本地备份安全可靠", "提示：无论归档源选择本地还是云端，归档成功的照片都会从小米云端删除，请确保归档文件夹安全可靠")
p.write_text(s)
