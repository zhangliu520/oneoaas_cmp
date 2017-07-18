#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
function:vcenter manage
"""
import time
from pygments.styles import vim
from pyVim.connect import SmartConnectNoSSL, Disconnect
from pyVmomi import vim, vmodl

from common.log import logger

#打印虚拟机对象
def PrintVmInfo(vm, depth=1):
    """
    Print information for a particular virtual machine or recurse into a folder
    or vApp with depth protection
    """
    maxdepth = 10

    # if this is a group it will have children. if it does, recurse into them
    # and then return
    if hasattr(vm, 'childEntity'):
        if depth > maxdepth:
            return
        vmList = vm.childEntity
        for c in vmList:
            PrintVmInfo(c, depth+1)
        return

    # if this is a vApp, it likely contains child VMs
    # (vApps can nest vApps, but it is hardly a common usecase, so ignore that)
    if isinstance(vm, vim.VirtualApp):
        vmList = vm.vm
        for c in vmList:
            PrintVmInfo(c, depth + 1)
        return

    summary = vm.summary
    print("Name       : ", summary.config.name)
    print("Path       : ", summary.config.vmPathName)
    print("Guest      : ", summary.config.guestFullName)
    annotation = summary.config.annotation
    if annotation != None and annotation != "":
        print("Annotation : ", annotation)
    print("State      : ", summary.runtime.powerState)
    if summary.guest != None:
        ip = summary.guest.ipAddress
        if ip != None and ip != "":
            print("IP         : ", ip)
    if summary.runtime.question != None:
        print("Question  : ", summary.runtime.question.text)
    print("")

class VmManage(object):

    def __init__(self,host,user,password,port,ssl):
        self.host = host
        self.user = user
        self.pwd = password
        self.port = port
        self.sslContext = ssl
        self.client = SmartConnectNoSSL(host=host,
                                      user=user,
                                      pwd=password,
                                      port=int(port)
                                    )
        self.content = self.client.RetrieveContent()

        if not self.client:
           raise Exception("构建虚拟机管理器失败")

    #vcenter执行动作等待
    def wait_for_task(self,task):
        """ wait for a vCenter task to finish """
        task_done = False
        while not task_done:
            if task.info.state == 'success':
                return task.info.result

            if task.info.state == 'error':
                print "there was an error"
                task_done = True

    #根据资源类型和名称，获取资源对象
    def _get_obj(self, vimtype, name):
        """
        Get the vsphere object associated with a given text name
        """
        obj = None
        content = self.client.RetrieveContent()
        container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
        for c in container.view:
            if c.name == name:
                obj = c
                break
        return obj

    def _get_all_objs(self,vimtype):
        """
        Get all the vsphere objects associated with a given type
        """
        obj = {}
        container = self.content.viewManager.CreateContainerView(self.content.rootFolder, vimtype, True)
        for c in container.view:
            obj.update({c: c.name})
        return obj


    def login_in_guest(self,username, password):
        return vim.vm.guest.NamePasswordAuthentication(username=username,password=password)

    def start_process(self,si, vm, auth, program_path, args=None, env=None, cwd=None):
        cmdspec = vim.vm.guest.ProcessManager.ProgramSpec(arguments=args, programPath=program_path, envVariables=env, workingDirectory=cwd)
        cmdpid = si.content.guestOperationsManager.processManager.StartProgramInGuest(vm=vm, auth=auth, spec=cmdspec)
        return cmdpid

    def is_ready(self,vm):

        while True:
            system_ready = vm.guest.guestOperationsReady
            system_state = vm.guest.guestState
            system_uptime = vm.summary.quickStats.uptimeSeconds
            if system_ready and system_state == 'running' and system_uptime > 90:
                break
            time.sleep(10)

    def get_vm_by_name(self,name):
        """
        Find a virtual machine by it's name and return it
        """

        return self._get_obj([vim.VirtualMachine], name)

    def get_host_by_name(self, name):
        """
        Find a virtual machine by it's name and return it
        """

        return self._get_obj([vim.HostSystem], name)

    def get_resource_pool(self, name):
        """
        Find a virtual machine by it's name and return it
        """

        return self._get_obj([vim.ResourcePool], name)

    def get_resource_pools(self):
        """
        Returns all resource pools
        """
        return self._get_all_objs([vim.ResourcePool])

    def get_cluster_pools(self):
        """
        Returns all resource pools
        """
        return self._get_all_objs([vim.ClusterComputeResource])

    def get_datastores(self):
        """
        Returns all datastores
        """
        return self._get_all_objs([vim.Datastore])

    def get_datastores_info(self):
        content = self.client.RetrieveContent()
        # Search for all ESXi hosts

        objview = content.viewManager.CreateContainerView(content.rootFolder,
                                                          [vim.HostSystem],
                                                          True)
        #获取主机视图
        esxi_hosts = objview.view
        objview.Destroy()

        datastores = {}
        datastores_all_capacity = 0
        for esxi_host in esxi_hosts:

            # All Filesystems on ESXi host
            storage_system = esxi_host.configManager.storageSystem
            host_file_sys_vol_mount_info = \
                storage_system.fileSystemVolumeInfo.mountInfo

            datastore_dict = {}
            # Map all filesystems
            for host_mount_info in host_file_sys_vol_mount_info:
                # Extract only VMFS volumes
                if host_mount_info.volume.type == "VMFS":
                    extents = host_mount_info.volume.extent
                    datastore_details = {
                        'uuid': host_mount_info.volume.uuid,
                        'capacity': host_mount_info.volume.capacity,
                        'vmfs_version': host_mount_info.volume.version,
                        'local': host_mount_info.volume.local,
                        'ssd': host_mount_info.volume.ssd
                    }
                    datastores_all_capacity+=host_mount_info.volume.capacity

                    extent_arr = []
                    for extent in extents:
                        # create an array of the devices backing the given
                        # datastore
                        extent_arr.append(extent.diskName)
                        # add the extent array to the datastore info
                        datastore_details['extents'] = extent_arr
                        # associate datastore details with datastore name
                        datastore_dict[host_mount_info.volume.name] = datastore_details

            # associate ESXi host with the datastore it sees
            datastores[esxi_host.name] = datastore_dict
            datastores['datastores_all_capacity'] = datastores_all_capacity

        return datastores

    def get_hosts(self):
        """
        Returns all hosts
        """
        return self._get_all_objs([vim.HostSystem])

    def get_hosts_array(self):
        host_view = self.content.viewManager.CreateContainerView(self.content.rootFolder,
                                                            [vim.HostSystem],
                                                            True)
        obj = [host for host in host_view.view]
        host_view.Destroy()
        return obj

    def get_datacenters(self):
        """
        Returns all datacenters
        """
        return self._get_all_objs([vim.Datacenter])

    def get_registered_vms(self):
        """
        Returns all vms
        """
        return self._get_all_objs([vim.VirtualMachine])

    def get_dvs_distributed_virtual_portgroup(self,network_name):
        objview = self.content.viewManager.CreateContainerView(self.content.rootFolder,
                                                          [vim.dvs.DistributedVirtualPortgroup],
                                                          True)
        obj = None
        for view in objview.view:
            if view.name == network_name:
                obj = view
                break
        objview.Destroy()
        return obj

    #获取主机端口组
    def get_hosts_portgroups(self,hosts):
        hostPgDict = {}
        for host in hosts:
            pgs = host.config.network.portgroup
            print pgs
            hostPgDict[host] = pgs
        return hostPgDict

    #获取overheadMemory
    def get_overhead_memory(self,vm,host):
        overheadMemory = self.content.overheadMemoryManager.LookupVmOverheadMemory(vm,host)
        print overheadMemory
        return overheadMemory

    #获取dvs的特性
    def get_dvs_featurecapability(self):
        dvsFeature = {}
        dVSFeatureCapability = self.content.dvSwitchManager.QueryDvsFeatureCapability()
        dvsFeature['ipFix'] = dVSFeatureCapability.ipfixSupported
        dvsFeature['vspan'] = dVSFeatureCapability.vspanSupported
        dvsFeature['vmDirectPathGen2'] = dVSFeatureCapability.vmDirectPathGen2Supported
        dvsFeature['multicastSnooping'] = dVSFeatureCapability.multicastSnoopingSupported
        return  dvsFeature

    #获取虚拟机网卡信息
    def get_vm_nics(self,vm):

        hosts = self.get_hosts_array()
        for dev in vm.config.hardware.device:

            if isinstance(dev, vim.vm.device.VirtualEthernetCard):
                dev_backing = dev.backing
                portGroup = None
                vlanId = None
                vSwitch = None

                if hasattr(dev_backing, 'network'):
                    # portGroupKey = dev.backing.port.portgroupKey
                    # dvsUuid = dev.backing.port.switchUuid
                    portGroup = dev.backing.network.name
                    network = self.get_dvs_distributed_virtual_portgroup(portGroup)
                    print network
                    # for p in pgs:
                    #     vlanId = str(p.spec.vlanId)
                    #     vSwitch = str(p.spec.vswitchName)
                    #     print vlanId
                    #     print vSwitch
                    # try:
                    #     #查询分布式交换机
                    #     dvs = self.content.dvSwitchManager.QueryDvsByUuid(dvsUuid)
                    #     print dvs
                    # except:
                    #     portGroup = "** Error: DVS not found **"
                    #     vlanId = "NA"
                    #     vSwitch = "NA"
                    # else:
                    #     pgObj = dvs.LookupDvPortGroup(portGroupKey)
                    #     portGroup = pgObj.config.name
                    #     vlanId = str(pgObj.config.defaultPortConfig.vlan.vlanId)
                    #     vSwitch = str(dvs.name)



    #分析网络流浪
    def get_flows_info(self):
        """
        获取网卡流量信息
        """
        vms = self.get_vms()
        for vm in vms:
            if vm is not None:
                self.get_vm_nics(vm)




    #获取虚拟机列表
    def get_vms(self):
        content = self.client.content
        objView = content.viewManager.CreateContainerView(content.rootFolder,[vim.VirtualMachine],True)
        vmList = objView.view
        # vmAllList = []
        # content = self.client.RetrieveContent()
        # for child in content.rootFolder.childEntity:
        #     if hasattr(child, 'vmFolder'):
        #         datacenter = child
        #         vmFolder = datacenter.vmFolder
        #         vmList = vmFolder.childEntity
        #         vmAllList.append(vmList)

        return vmList

    #创建
    def create(self):
        pass

    #克隆
    def clone(self,template,vm_name,datacenter_name,vm_folder,datastore_name,cluster_name,resource_pool,power_on):

        #选择克隆的虚拟机存放位置,通过数据中心获取对象
        datacenter = self._get_obj([vim.Datacenter], datacenter_name)
        if vm_folder:
            destfolder = self._get_obj([vim.Folder], vm_folder)
        else:
            destfolder = datacenter.vmFolder

        if datastore_name:
            datastore = self._get_obj([vim.Datastore], datastore_name)
        else:
            datastore = self._get_obj([vim.Datastore], template.datastore[0].info.name)

        # if None, get the first one
        cluster = self._get_obj([vim.ClusterComputeResource], cluster_name)
        if resource_pool:
            resource_pool = self._get_obj([vim.ResourcePool], resource_pool)
        else:
            resource_pool = cluster.resourcePool

        relospec = vim.vm.RelocateSpec()
        relospec.datastore = datastore
        relospec.pool = resource_pool

        clonespec = vim.vm.CloneSpec()
        clonespec.location = relospec
        clonespec.powerOn = power_on

        print "cloning VM..."
        task = template.Clone(folder=destfolder, name=vm_name, spec=clonespec)

        return self.wait_for_task(task)



    #关闭虚拟机
    def stop(self,vmnames):
        print 'vm manage stop...'
        content = self.client.content
        objView = content.viewManager.CreateContainerView(content.rootFolder,
                                                          [vim.VirtualMachine],
                                                          True)
        vmList = objView.view
        objView.Destroy()

        # Find the vm and power it on
        tasks = [vm.PowerOff() for vm in vmList if vm.name in vmnames]

        from pyVim.task import WaitForTasks
        WaitForTasks(tasks=tasks,si=self.client)

    #开启
    def start(self,vmnames):
        print 'vm manage start...'
        # content = self.client.content
        # objView = content.viewManager.CreateContainerView(content.rootFolder,
        #                                                   [vim.VirtualMachine],
        #                                                   True)
        # vmList = objView.view
        # objView.Destroy()


        # tasks = [vm.PowerOn() for vm in vmList if vm.name in vmnames]
        #
        # print tasks
        #
        # from pyvim.task import WaitForTasks
        # WaitForTasks(tasks=tasks,si=self.client)

        vm = self.get_vm_by_name(self.client, vmnames)
        try:
            print "find vm and start vm ..."
            vm.PowerOnGuest()
        except:
            # forceably shutoff/on
            # need to do if vmware guestadditions isn't running
            vm.ResetVM_Task()

        Disconnect(self.client)


    #重启
    def reboot(self,vmnames):
        print 'vm manage reboot...'
        vm = self.get_vm_by_name(self.client, vmnames)
        try:
            vm.RebootGuest()
        except:
            # forceably shutoff/on
            # need to do if vmware guestadditions isn't running
            vm.ResetVM_Task()

        Disconnect(self.client)


