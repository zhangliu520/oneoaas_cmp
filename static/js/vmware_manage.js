/**
 * Created by heidsoft on 2017/6/16.
 * @description vcenter配置操作模块
 */

//vcenter 管理插件
var VCenterManage = (function ($,toastr) {
    return {
        //初始化虚拟机表格对象
        vmTable:null,
        //被选择记录ID
        selectedRows:[],
        //初始化虚拟机表格
        init:function (tableId) {

            var language = {
                search: '搜索：',
                lengthMenu: "每页显示 _MENU_ 记录",
                zeroRecords: "没找到相应的数据！",
                info: "分页 _PAGE_ / _PAGES_",
                infoEmpty: "暂无数据！",
                infoFiltered: "(从 _MAX_ 条数据中搜索)",
                paginate: {
                    first: '<<',
                    last: '>>',
                    previous: '上一页',
                    next: '下一页',
                }
            }

            var VCenterManageRecord = $(tableId).DataTable({
                paging: true, //隐藏分页
                ordering: false, //关闭排序
                info: false, //隐藏左下角分页信息
                searching: false, //关闭搜索
                pageLength : 5, //每页显示几条数据
                lengthChange: false, //不允许用户改变表格每页显示的记录数
                language: language, //汉化
                sLoadingRecords:true,
                ajax: {
                    url: site_url+'vmware/api/getVcenterVirtualMachineList',
                },
                'columnDefs': [
                    {
                        'targets': 0,
                        'className': 'dt-head-center dt-body-center',
                        'checkboxes': {
                            'selectRow': true
                        }
                    }
                ],
                // select: {
                //     style:    'os',
                //     selector: 'td:first-child'
                // },
                //多选
                'select': {
                    'style': 'multi'
                },
                columns: [
                    {
                        data: "id",
                    },
                    {
                        title : '名称',
                        data: "name",
                    },
                    {
                        title : '内存(MB)',
                        data: "memorySizeMB",
                    },
                    {
                        title : 'CPU个数',
                        data: "numCpu",
                    },
                    {
                        title : '最大CPU使用',
                        data: "maxCpuUsage",
                    },
                    {
                        title : '最大内存使用',
                        data: "maxMemoryUsage",
                    },
                    {
                        title : '是否为模板',
                        data: "template",
                        render: function ( data, type, row ) {
                            if(data === false){
                                return "不是模板";
                            }else{
                                return "是模板";
                            }

                        },
                    },
                    {
                        title : '系统类型',
                        data: "guest_fullname",
                    },
                    {
                        title : '运行状态',
                        data: "power_state",
                        render: function ( data, type, row ) {
                            if(data === 'poweredOn'){
                                return "运行";
                            }else if(data === 'poweredOff'){
                                return "关机";
                            }

                        },
                    },
                    {
                        title : '总体状态',
                        data: "overallStatus",
                        render: function ( data, type, row ) {
                            if(data === 'green'){
                                return "正常";
                            }else{
                                return data;
                            }
                        },
                    },
                    {
                        title : 'IP',
                        data: "ipaddress",
                    },

                    {
                        title : '操作',
                        data: "name",
                        render: function ( data, type, row ) {
                            var opHTML='<button class="btn btn-xs btn-danger" onclick="VCenterManage.snapshot()">执行快照</button>';
                            return opHTML;
                        },
                    },
                ],
            });


            this.vmTable = VCenterManageRecord;

            //设置button
            new $.fn.dataTable.Buttons( VCenterManageRecord, {
                buttons: [
                    {
                        extend: 'copyHtml5',
                        text: '拷贝表格'
                    },
                    {
                        extend: 'excelHtml5',
                        text: '导出Excel'
                    },
                    {
                        extend: 'pdfHtml5',
                        text: '导出PDF'
                    },
                    {
                        extend: 'csvHtml5',
                        text: '导出CVS'
                    },
                ],
            } );

            //将button放置到底部
            var tableContainer = VCenterManageRecord.buttons().container();
            tableContainer.appendTo(
                VCenterManageRecord.table().container()
            );

            return VCenterManageRecord;
        },
        //操作动作前置条件
        beforeAction:function(){
            var rows_selected = this.vmTable.column(0).checkboxes.selected();
            if(typeof rows_selected === 'undefined' || rows_selected.length === 0){
                toastr.warning("请选择虚拟机资源");
                return false
            }
            var rowIds = this.selectedRows =[];
            $.each(rows_selected, function(index, rowId){
                rowIds.push(rowId);
            });
            this.selectedRows = rowIds;
            return true
        },
        //创建虚拟机
        create:function () {
            toastr.warning("这是高级功能，蓝鲸社区版暂不支持该功能,如果需要请联系OneOaaS");

            return

            // $.ajax({
            //     url: site_url+'vmware/api/create',
            //     type: 'post',
            //     dataType:'json',
            //     data: {
            //         "vmId":this.selectedRows,
            //     },
            //     success: function (data) {
            //         toastr.success(data.message);
            //     }
            // });
            // $('#createVmWizard').modal('show');
        },
        //克隆虚拟机
        clone:function () {
            if(!this.beforeAction()){
                return
            }
            if(this.selectedRows.length>1){
                toastr.warning("蓝鲸版克隆操作只支持选择一台虚拟机");
                return
            }

            $('#cloneVmWizard').modal('show');

        },
        //执行克隆
        executeClone:function () {
            var cloneVmName = $("#cloneVmName").val();
            var select_datacenter = $("#select_datacenter .select2_box").select2("val");
            var select_cluster = $("#select_cluster .select2_box").select2("val");
            var select_datastore = $("#select_datastore .select2_box").select2("val");
            $.ajax({
                url: site_url+'vmware/api/clone',
                type: 'post',
                dataType:'json',
                data: {
                    "vmId":this.selectedRows[0],
                    "vmName":cloneVmName,
                    "vmDatacenter":select_datacenter,
                    "vmCluster":select_cluster,
                    "vmDatastore":select_datastore,
                },
                success: function (data) {
                    $('#cloneVmWizard').modal('hide');
                    toastr.success(data.message);
                    VCenterManage.vmTable.ajax.reload( null, false );

                }
            });
        },
        //关闭虚拟机
        poweroff: function (data) {
            if(!this.beforeAction()){
                return
            }

            if(this.selectedRows.length>1){
                toastr.warning("蓝鲸版关机操作只支持一台虚拟机");
                return
            }
            $.ajax({
                url: site_url+'vmware/api/poweroff',
                type: 'post',
                dataType: 'json',
                data: {
                    "vmId":this.selectedRows[0],
                },
                success: function (data) {
                    toastr.success(data.message);
                    //重新刷新表格数据
                    VCenterManage.vmTable.ajax.reload( null, false );
                }
            });
        },
        //开启虚拟机
        start: function (data) {
            if(!this.beforeAction()){
                return
            }
            if(this.selectedRows.length>1){
                toastr.warning("蓝鲸版开机操作只支持一台虚拟机");
                return
            }
            $.ajax({
                url: site_url+'vmware/api/start',
                type: 'post',
                dataType: 'json',
                data: {
                    "vmId":this.selectedRows[0],
                },
                success: function (data) {
                    toastr.success(data.message);
                    VCenterManage.vmTable.ajax.reload( null, false );
                }
            });
        },
        //重启虚拟机
        reboot: function (data) {
            if(!this.beforeAction()){
                return
            }
            if(this.selectedRows.length>1){
                toastr.warning("蓝鲸版重启操作只支持一台虚拟机");
                return
            }
            $.ajax({
                url: site_url+'vmware/api/reboot',
                type: 'post',
                dataType: 'json',
                data: {
                    "vmId":this.selectedRows[0],
                },
                success: function (data) {
                    toastr.success(data.message);
                    VCenterManage.vmTable.ajax.reload( null, false );
                }
            });
        },
        //销毁虚拟机
        destroy: function (data) {
            if(!this.beforeAction()){
                return
            }
            if(this.selectedRows.length>1){
                toastr.warning("蓝鲸版销毁操作只支持一台虚拟机");
                return
            }
            $.ajax({
                url: site_url+'vmware/api/destroy',
                type: 'post',
                dataType: 'json',
                data: {
                    "vmId":this.selectedRows[0],
                },
                success: function (data) {
                    toastr.success(data.message);
                    VCenterManage.vmTable.ajax.reload( null, false );
                }
            });
        },
        snapshot:function () {
            toastr.warning("这是高级功能，蓝鲸社区版暂不支持该功能,如果需要请联系OneOaaS");
        },
        //同步虚拟机
        async: function (data) {
            if(!this.beforeAction()){
                return
            }
            $.ajax({
                url: site_url+'vmware/api/asyncDemo',
                type: 'post',
                dataType: 'json',
                data: {
                    "id":this.selectedRows[0],
                },
                success: function (data) {
                    toastr.success(data.message);
                    VCenterManage.vmTable.ajax.reload( null, false );
                }
            });
        },
        //webssh控制台
        webssh:function () {
            toastr.warning("这是高级功能，蓝鲸社区版暂不支持该功能,如果需要请联系OneOaaS");
            return
        },
        RDP:function () {
            toastr.warning("这是高级功能，蓝鲸社区版暂不支持该功能,如果需要请联系OneOaaS");
            return
        }
    }
})($,window.toastr);

//扩展到jquery
//$.fn.extend(VCenterManage);
//扩展函数


$(document).ready(function(){

    $("#ccAppList .select2_box").select2({
        ajax: {
            url: site_url+"vmware/api/getAppList",
            cache: false,
            //对返回的数据进行处理
            results: function(data){
                console.log(data);
                return data;
            }
        }
    })

    $("#select_datacenter .select2_box").select2({
        ajax: {
            url: site_url+"vmware/api/getAllDatacenter",
            cache: false,
            //对返回的数据进行处理
            results: function(data){
                console.log(data);
                return data;
            }
        }
    })

    $("#select_cluster .select2_box").select2({
        ajax: {
            url: site_url+"vmware/api/getAllCluster",
            cache: false,
            //对返回的数据进行处理
            results: function(data){
                console.log(data);
                return data;
            }
        }
    })

    $("#select_datastore .select2_box").select2({
        ajax: {
            url: site_url+"vmware/api/getAllDatastore",
            cache: false,
            //对返回的数据进行处理
            results: function(data){
                console.log(data);
                return data;
            }
        }
    })


    $('#createVmWizard').bootstrapWizard(
        {
            tabClass: 'nav nav-pills',
            onNext: function(tab, navigation, index) {
                console.log("onNext:"+index);
                console.log(navigation);
                console.log(tab);
                if(index==4){
                    //$('#rootwizard').bootstrapWizard('display', $('#stepid').val());
                }
            },
            onPrevious:function(tab, navigation, index) {
                console.log("onPrevious"+index);
                console.log("onPrevious"+index);
            }
        }
    );

    $('#rootwizard .finish').click(function() {
        alert('Finished!, Starting over!');
        //$('#rootwizard').find("a[href*='tab1']").trigger('click');
    });

    VCenterManage.init('#vcenter_manage_record');

})




