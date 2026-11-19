import fs from 'node:fs/promises';
import { createRequire } from 'node:module';
import {pathToFileURL,fileURLToPath} from 'node:url';
const require = createRequire('C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json');
const {Workbook, SpreadsheetFile} = await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const csv = await fs.readFile(new URL('../data/heart-disease-four-site.csv', import.meta.url), 'utf8');
const wb = await Workbook.fromCSV(csv, {sheetName:'原始数据'});
const raw = wb.worksheets.getItem('原始数据');
const data = raw.getRange('A2:P921').values;
for (const row of data) for (let j=2;j<16;j++) row[j] = row[j] === '' || row[j] === null ? null : Number(row[j]);
raw.getRange('A2:P921').values = data;
const s = wb.worksheets.add('改名实验');
s.getRange('A2').values = [['胸痛类别改名实验']];
s.getRange('A4:E4').values = [['原编号','新编号','原类别人数','改名后人数','人数差']];
s.getRange('A5:B8').values = [[1,10],[2,20],[3,40],[4,80]];
for(let r=5;r<=8;r++) s.getRange(`C${r}:E${r}`).formulas = [[`=COUNTIFS(C19:C938,A${r})`,`=COUNTIFS(D19:D938,B${r})`,`=D${r}-C${r}`]];
s.getRange('A10:C10').values = [['比较项目','原编号','新编号']];
s.getRange('A11:A12').values = [['编码均值'],['有效记录数']];
s.getRange('B11:C12').formulas = [['=AVERAGE(C19:C938)','=AVERAGE(D19:D938)'],['=COUNT(C19:C938)','=COUNT(D19:D938)']];
s.getRange('A14').values = [['结论：编号均值随编码改变，同一类别人数保持不变。']];
s.getRange('A15').values = [['胸痛类别属于分类变量，编号均值不能解释为平均胸痛程度。']];
s.getRange('A16').values = [['数据：heart-disease-four-site.csv；保留全部920条记录，cp无缺失。']];
s.getRange('A18:D18').values = [['记录编号','数据中心','原胸痛编号','改名后编号']];
s.getRange('A19:C938').values = data.map(row=>[row[0],row[1],row[4]]);
s.getRange('D19:D938').formulas = data.map((_,i)=>[`=VLOOKUP(C${i+19},$A$5:$B$8,2,FALSE)`]);
for(const sheet of [raw,s]) {
  sheet.showGridLines=false;
  sheet.getUsedRange().format.font.name='Microsoft YaHei';
  sheet.getUsedRange().format.font.size=11;
  sheet.getUsedRange().format.rowHeight=23;
  sheet.getUsedRange().format.verticalAlignment='center';
}
raw.getRange('A1:P1').format.fill='#243E58';
raw.getRange('A1:P1').format.font.color='#FFFFFF';
raw.getRange('A1:P1').format.font.bold=true;
raw.getRange('A1:B921').format.columnWidth=22;
raw.getRange('C1:P921').format.columnWidth=13;
raw.freezePanes.freezeRows(1);
s.getRange('A1:E938').format.columnWidth=21;
s.getRange('B1:B938').format.columnWidth=24;
s.getRange('A2').format.font.size=16;
s.getRange('A2').format.font.bold=true;
s.getRange('B11:C11').setNumberFormat('0.0000');
s.getRange('A5:B8').format.fill='#FFF2CC';
s.getRange('D19:D938').format.fill='#EEF3F8';
for(const a of ['A4:E4','A10:C10','A18:D18']) {
  s.getRange(a).format.fill='#243E58';
  s.getRange(a).format.font.color='#FFFFFF';
  s.getRange(a).format.font.bold=true;
}
s.freezePanes.freezeRows(18);
wb.recalculate();
const counts=[1,2,3,4].map(k=>data.filter(r=>r[4]===k).length);
const mean=data.reduce((a,r)=>a+r[4],0)/data.length;
const newMean=data.reduce((a,r)=>a+[10,20,40,80][r[4]-1],0)/data.length;
const got=s.getRange('B11:C12').values;
if(Math.abs(got[0][0]-mean)>1e-9 || Math.abs(got[0][1]-newMean)>1e-9 || got[1][0]!==920 || got[1][1]!==920) throw Error('均值或记录数核验失败');
const freq=s.getRange('C5:E8').values;
if(freq.some((r,i)=>r[0]!==counts[i] || r[1]!==counts[i] || r[2]!==0)) throw Error('频数核验失败');
console.log(JSON.stringify({records:data.length,counts,mean,newMean}));
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!',options:{useRegex:true,maxResults:10},maxChars:1200})).ndjson);
await (await SpreadsheetFile.exportXlsx(wb)).save(fileURLToPath(new URL('胸痛类别改名实验.xlsx',import.meta.url)));
for(const [sheetName,range,file] of [['改名实验','A1:E22','recoding-preview.png'],['原始数据','A1:H8','source-preview.png']]) {
  const preview=await wb.render({sheetName,range,scale:1.5,format:'png'});
  await fs.writeFile(new URL(file,import.meta.url),new Uint8Array(await preview.arrayBuffer()));
}
