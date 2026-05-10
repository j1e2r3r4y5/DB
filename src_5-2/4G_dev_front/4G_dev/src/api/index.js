import request from '../utils/request'

const api = {
    login(data) {
        return request({
            url: '/login',
            method: 'POST',
            data
        })
    },
    getDeviceList(data) {
        return request({
            url: '/get-devicelist',
            method: 'POST',
            data
        })
    },
    getUserList(data) {
        return request({
            url: '/user',
            method: 'POST',
            data
        })
    },
    Adddevice(data) {
        return request({
            url: '/add/device',
            method: 'POST',
            data
        })
    },
    ModifyDevice(data) {
        return request({
            url: '/modify-device',
            method: 'POST',
            data
        })
    },
    DeleteDevice(data) {
        return request({
            url: '/remove/device',
            method: 'POST',
            data
        })
    },
    Modifyuser(data) {
        return request({
            url: '/modifyuser',
            method: 'POST',
            data
        })
    },
    Permuser(data) {
        return request({
            url: '/Permuser',
            method: 'POST',
            data
        })
    },
    Registeruser(data) {
        return request({
            url: '/register',
            method: 'POST',
            data
        })
    },
    Deleteuser(data) {
        return request({
            url: '/remove-user',
            method: 'POST',
            data
        })
    },
    Changeuser(data) {
        return request({
            url: '/change-user',
            method: 'POST',
            data
        })
    },
    logout() {
        return request({
            url: '/logout',
            method: 'POST'
        })
    },
    getvariables(data) {
        return request({
            url: '/getvariables',
            method: 'POST',
            data
        })
    },
    addvariable(data) {
        return request({
            url: '/addvariable',
            method: 'POST',
            data
        })
    },
    modifyvariable(data) {
        return request({
            url: '/updatevariable',
            method: 'POST',
            data
        })
    },
    deletevariable(data) {
        return request({
            url: '/deletevariable',
            method: 'POST',
            data
        })
    },
    getvarbydeviceid(data) {
        return request({
            url: '/getvarbydeviceid',
            method: 'POST',
            data
        })
    },
    downpayload(data) {
        return request({
            url: '/payload',
            method: 'POST',
            data
        })
    },
    query(data) {
        return request({
            url: '/query',
            method: 'POST',
            data
        })
    },
    recoveryvariable(data) {
        return request({
            url: '/recoveryvariable',
            method: 'POST',
            data
        })
    },
    dataquery(data) {
        return request({
            url: '/dataquery',
            method: 'POST',
            data
        })
    },
    Getdata(data) {
        return request({
            url: '/data',
            method: 'POST',
            data
        })
    },
    alldata(data) {
        return request({
            url: '/alldata',
            method: 'POST',
            data
        })
    },

    // ==========================================
    // 方案2：JSON接口（新增）
    // ==========================================

    // 下发模组配置
    sendModuleConfig(data) {
        return request({
            url: '/sendcod/module-config',
            method: 'POST',
            data
        })
    },

    // 下发数据配置
    sendDataConfig(data) {
        return request({
            url: '/sendcod/data-config',
            method: 'POST',
            data
        })
    },

    // 查询数据配置
    queryDataConfig(data) {
        return request({
            url: '/sendcod/query-config',
            method: 'POST',
            data
        })
    },

    // 远程置数
    remoteWrite(data) {
        return request({
            url: '/sendcod/remote-write',
            method: 'POST',
            data
        })
    },

    // 查询沙箱数据
    sandboxDataQuery(data) {
        return request({
            url: '/sandbox/dataquery',
            method: 'POST',
            data
        })
    },

    // 批量导入变量
    batchAddvariable(data) {
        return request({
            url: '/batch-addvariable',
            method: 'POST',
            data
        })
    },

    // ==========================================
    // 监控相关接口
    // ==========================================

    // 获取系统健康状态
    getHealth() {
        return request({
            url: '/health',
            method: 'GET'
        })
    },

    // 获取系统统计数据
    getStats() {
        return request({
            url: '/stats',
            method: 'GET'
        })
    }
}

export default api