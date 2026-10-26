import {deflateSync} from 'node:zlib';
// Original geometric CFP+ placeholder icon; generated locally without dependencies.
export function iconPNG(size) {
  const crc = bytes => {
    let n = 0xffffffff;
    for (const b of bytes) { n ^= b; for (let i=0;i<8;i++) n=(n>>>1)^((n&1)?0xedb88320:0); }
    return (n^0xffffffff)>>>0;
  };
  const chunk = (type,data) => {
    const t=Buffer.from(type),len=Buffer.alloc(4),sum=Buffer.alloc(4);
    len.writeUInt32BE(data.length);sum.writeUInt32BE(crc(Buffer.concat([t,data])));
    return Buffer.concat([len,t,data,sum]);
  };
  const header=Buffer.alloc(13);header.writeUInt32BE(size);header.writeUInt32BE(size,4);header[8]=8;header[9]=2;
  const rows=Buffer.alloc((size*3+1)*size);
  for(let y=0;y<size;y++)for(let x=0;x<size;x++) {
    const plus=(Math.abs(x-size/2)<size*.09&&Math.abs(y-size/2)<size*.28)||(Math.abs(y-size/2)<size*.09&&Math.abs(x-size/2)<size*.28);
    const offset=y*(size*3+1)+1+x*3;
    rows.set(plus?[210,244,134]:[21,62,53],offset);
  }
  return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',header),chunk('IDAT',deflateSync(rows)),chunk('IEND',Buffer.alloc(0))]);
}
