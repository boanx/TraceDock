"""Read EXLab v8 TDMBIN measurements without a CSV intermediate."""
import math
from pathlib import Path
import struct

import numpy as np


def read_tdmbin(path, progress=None, check_cancel=None):
    path = Path(path)
    def checkpoint():
        if check_cancel is not None:
            check_cancel()
    def exact(stream, length):
        result = stream.read(length)
        if len(result) != length:
            raise ValueError('TDMBIN dosyası eksik veya okunurken değişmiş.')
        return result
    def text(value):
        value = value.split(b'\0', 1)[0]
        try:
            return value.decode('utf-8')
        except UnicodeDecodeError:
            return value.decode('cp1254', errors='replace')

    checkpoint()
    with path.open('rb') as stream:
        size = stream.seek(0, 2)
        stream.seek(0)
        header = exact(stream, 84)
        u32 = lambda offset: struct.unpack_from('<I', header, offset)[0]
        u64 = lambda offset: struct.unpack_from('<Q', header, offset)[0]
        identifier, version = u32(0), u32(4)
        if identifier != 20100225:
            raise ValueError('Dosya desteklenen Exlab TDMBIN imzasını taşımıyor.')
        if version != 8:
            raise ValueError(f'TDMBIN sürümü {version} desteklenmiyor. Şu anda sürüm 8 okunabiliyor; Exlab üzerinden CSV dışa aktarabilirsiniz.')
        arrangement, datatype = struct.unpack_from('<HH', header, 12)
        count, repeat = u32(16), u32(20)
        rate = struct.unpack_from('<d', header, 32)[0]
        info_offset, data_offset = u64(48), u32(56)
        package_count, first_index, last_count = u32(60), u32(64), u32(68)
        time_index = struct.unpack_from('<i', header, 72)[0]
        if arrangement not in (0, 1) or datatype != 5:
            raise ValueError(f'Desteklenmeyen TDMBIN veri düzeni/türü: {arrangement}/{datatype}. Sürüm 8 double verileri desteklenir.')
        if count <= 0 or not math.isfinite(rate) or rate <= 0:
            raise ValueError('TDMBIN kanal sayısı veya örnekleme hızı geçersiz.')
        if not (84 <= info_offset < data_offset <= size) or data_offset-info_offset != count*182:
            raise ValueError('TDMBIN kanal bilgisi bölümü desteklenen 182 baytlık kayıt düzeniyle uyuşmuyor.')
        if time_index != -1 and not 0 <= time_index < count:
            raise ValueError('TDMBIN zaman kanalı indeksi geçersiz.')
        payload_size = size-data_offset
        if payload_size == 0 or payload_size % (8*count):
            raise ValueError('TDMBIN ölçüm bölümü boş veya eksik.')
        samples = payload_size//(8*count)
        block_length = repeat if arrangement else 1
        if block_length <= 0:
            raise ValueError('TDMBIN blok uzunluğu geçersiz.')
        full, tail = divmod(samples, block_length)
        if arrangement and (package_count != full+bool(tail) or last_count != (tail or block_length)):
            raise ValueError('TDMBIN paket sayıları dosyanın ölçüm boyutuyla uyuşmuyor.')

        stream.seek(info_offset)
        names, units, ids, metadata, seen = [], {}, {}, [], {}
        for channel in range(count):
            checkpoint()
            record = exact(stream, 182)
            name = text(record[:50]) or f'Kanal {channel+1}'
            original = name
            suffix = 1
            while name in seen:
                suffix += 1
                name = f'{original} ({suffix})'
            seen[name] = True
            names.append(name)
            units[name] = text(record[50:60])
            ids[name] = text(record[108:158]) or name
            metadata.append({'name': name, 'fields_60_108': struct.unpack_from('<6d', record, 60),
                             'fields_158_182': struct.unpack_from('<3d', record, 158)})

        checkpoint()
        values = [np.empty(samples, dtype=float) for _ in names]
        stream.seek(data_offset)
        # Batch ordinary blocks to about 8 MB. For unusually large blocks,
        # consume one channel at a time in bounded slices instead.
        batch_groups = max(1, (8*1024*1024)//(8*count*block_length))
        for group in range(0, full, batch_groups):
            checkpoint()
            groups = min(batch_groups, full-group)
            if count*block_length*8 > 8*1024*1024:
                for channel in range(count):
                    for offset in range(0, block_length, 65536):
                        checkpoint()
                        length = min(65536, block_length-offset)
                        start = group*block_length+offset
                        values[channel][start:start+length] = np.frombuffer(exact(stream, length*8), dtype='<f8')
                if progress:
                    progress(.95*(group+1)*block_length/samples, f'{(group+1)*block_length:,}/{samples:,} örnek • {count} kanal')
                continue
            chunk = np.frombuffer(exact(stream, groups*count*block_length*8), dtype='<f8').reshape(groups, count, block_length)
            start, stop = group*block_length, (group+groups)*block_length
            for channel in range(count):
                checkpoint()
                values[channel][start:stop] = chunk[:, channel, :].reshape(-1)
            if progress:
                progress(.95*stop/samples, f'{stop:,}/{samples:,} örnek • {count} kanal')
        if tail:
            checkpoint()
            for channel in range(count):
                for offset in range(0, tail, 65536):
                    checkpoint()
                    length = min(65536, tail-offset)
                    start = full*block_length+offset
                    values[channel][start:start+length] = np.frombuffer(exact(stream, length*8), dtype='<f8')

    clock = values[time_index] if time_index >= 0 else None
    if clock is not None:
        previous = None
        for start in range(0, samples, 65536):
            checkpoint()
            part = clock[start:start+65536]
            if not np.all(np.isfinite(part)) or np.any(np.diff(part) <= 0) or (previous is not None and part[0] <= previous):
                raise ValueError('TDMBIN zaman kanalı sonlu ve artan değerlerden oluşmuyor.')
            previous = part[-1]
    channels = {name: values[i] for i, name in enumerate(names) if i != time_index}
    if not channels:
        raise ValueError('TDMBIN dosyasında zaman dışında ölçüm kanalı bulunamadı.')
    if progress:
        progress(1, f'{samples:,} örnek • {len(channels)} ölçüm kanalı okundu')
    return {'name': path.name, 'path': str(path), 'source_kind': 'exlab_tdmbin',
            'channels': channels, '_base_channels': dict(channels),
            'units': {name: units[name] for name in channels},
            'ids': {name: ids[name] for name in channels},
            'multipliers': {name: 1.0 for name in channels},
            'x': clock, '_base_x': clock, 'xname': 'time', 'x_is_date': False,
            'grid_rate': rate, '_base_rate': rate,
            'tdmbin_metadata': {'version': version, 'first_index': first_index,
                                'channels': metadata, 'extra_factors_applied': False}}
