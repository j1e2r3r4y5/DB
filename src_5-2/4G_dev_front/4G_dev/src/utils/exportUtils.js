export function exportToTxt(content, filename) {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = filename
    document.body.appendChild(a); a.click(); document.body.removeChild(a)
    URL.revokeObjectURL(url)
}

export function exportToCsv(rows, filename) {
    const BOM = '\uFEFF'
    const content = rows.map(row =>
        row.map(cell => {
            if (typeof cell === 'string' && (cell.includes(',') || cell.includes('"') || cell.includes('\n'))) {
                return '"' + cell.replace(/"/g, '""') + '"'
            }
            return cell
        }).join(',')
    ).join('\n')
    const blob = new Blob([BOM + content], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = filename
    document.body.appendChild(a); a.click(); document.body.removeChild(a)
    URL.revokeObjectURL(url)
}

export function exportToJson(data, filename) {
    const content = JSON.stringify(data, null, 2)
    const blob = new Blob([content], { type: 'application/json;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = filename
    document.body.appendChild(a); a.click(); document.body.removeChild(a)
    URL.revokeObjectURL(url)
}

export function seedToTxt(seed, variables, filename) {
    const header = '种子: ' + seed + '\n'
    const body = variables.map((v, i) =>
        `变量${i + 1}: ${v.varName}, 数据类型: ${v.dataType}, Modbus类型: ${v.modbusType}, Modbus地址: ${v.modbusAddr}, 数据长度: ${v.data_len}`
    ).join('\n')
    exportToTxt(header + '---\n' + body, filename)
}
