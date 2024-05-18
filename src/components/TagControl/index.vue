<!-- eslint-disable no-unused-vars -->
<!-- eslint-disable no-unused-vars -->

<template>
  <div class="TagControlPanel">
    <div class="panelHead">
      <el-button class="returnHomeBut" v-show="editShow" size="mini" @click="confirm()">确定</el-button>
    </div>
    <div id="TagControlPanelDiv" class="panelBody" ref="TagControlPanelDiv">
      <div v-show="editShow" id="tagTree" class="tagEditDiv" ref="tagTree">

      </div>
      <div class="chartTooltip">
        <p>
          <br /><strong class="name"></strong>
        </p>
      </div>

    </div>
  </div>
</template>

<script>
import * as d3 from 'd3'
import { onMounted, ref } from 'vue';
import domtoimage from 'dom-to-image';
import tools from "@/utils/tools.js";
import { color } from 'd3';
import { _ } from 'core-js';

export default {
  props: ["curTag","state"],
  data() {
    return {
      colorMap: {},
      mcolor: [
        "rgb(255,60,60)",
        "rgb(155,20,100)",
        "rgb(255,83,255)",
        "rgb(200,100,50)",
        "rgb(235,135,162)",
        "rgb(200,200,102)",
        "rgb(255,178,101)",
        "rgb(63,151,134)",
        "rgb(83,155,255)",
        "rgb(50,200,120)",
        "rgb(2,50,200)",
        "rgb(0,122,244)",
        "rgb(150,122,244)",
        "rgb(168,168,255)",
        "rgb(200,200,200)",
      ],
      tableShow: false,
      editShow: true,
      LLMPreTags: [],
      chooseTagsId: '',
      tagsData: [],
      tableData: [],
      currentTagData: [],
      currentTagDataTree:[],
      currentTagDataTree_Redata:[],
      currentFile: '',
      currentFileTag: [],
      currentFileLLMTag: [],
      newTag: [],
      newTagIds:[],
      mergeSourceNodeId:"",
      mergeTagrgetNodeId:"",
      treeGTransformK:1,
      treeGTransformX:10,
      treeGTransformY:100,
    };
  },
  watch: {
    state(val){
    },
    curTag(val) {
    },
    currentFile(val) {
      this.getTagData()
      this.newTag = [];
      this.newTagIds = [];
      this.currentFileTag = val['tags'];
    },
    currentFileTag(val) {
      this.drawtagTree();
    },
    currentFileLLMTag(val) {
      this.currentFileTag = [...new Set([...this.currentFileTag, ...val])]
    },


    LLMPreTags(val) {
      console.log("tag", val);
      const _this = this;
      let tagsData = tools.deepClone(this.currentTagData);
      let tagsDataNow = tools.deepClone(this.currentTagDataTree_Redata);
      let tags = tagsData['subF'];
      let rootTag = tagsData['fields'];
      let tagsN = tagsDataNow['subF'];
      let rootTagN = tagsDataNow['fields'];
      console.log(tagsData,tags,rootTag)
      let keys = Object.keys(val);
      let tagIds = []
      let newTagIds = []
      let newTag = []
      keys.forEach((filed, idx) => {
        if (rootTag.indexOf(filed) != -1) {
          let rootField = tags.find((d) => { return d['tag'] == filed; });
          let filedTags = val[filed];
          tagIds.push(rootField['id']);
          let rootFieldSubTagName = rootField['subTagName'];
          let rootFieldSubTagId = rootField['subTag'];
          let newIDlen = rootFieldSubTagName.length + 1;
          let newTemp = {
            "id": rootField['id'],
            "newSub": [],
            "newSubName":[]
          }
          filedTags.forEach((ft) => {
            let nameIndex = rootFieldSubTagName.indexOf(ft)
            if (nameIndex != -1) {
              let tagid = rootFieldSubTagId[nameIndex];
              tagIds.push(tagid);
            }
            else {
              let newId = `${rootField['id']}_${newIDlen}`;
              tagIds.push(newId);
              newIDlen += 1;
              let temp = {
                "id": newId,
                "name": ft,
                "children": []
              }
              newTemp['newSub'].push(temp);
              newTagIds.push(newId);
              newTemp['newSubName'].push(ft);
            }
          })
          newTag.push(newTemp)
        }
      })
      this.currentFileLLMTag = tagIds;
      this.newTag = newTag;
      this.newTagIds = newTagIds;
      let treeData = tools.deepClone(this.currentTagDataTree);
      newTag.forEach((nt,idx)=>{
        let cId = nt['id'];
        treeData['children'].find((d)=>{return d['id'] == cId})['children'].push(...nt['newSub']);
      })
      this.currentTagDataTree = treeData;
      console.log(111,this.newTag,this.newTagIds,treeData)
    },
    currentTagDataTree(val){
      let fileds = [];
      let subF = [];
      let newData = this.traverseTree(-1,-1,val);
      console.log(val,newData)
      val['children'].forEach((fd,idx)=>{
        fileds.push(fd['name']);
        fd['id'] = `${idx+1}`
        let fTemp = {
          "id": fd['id'],
          "tag":fd['name'],
          "subTag":[],
          "subTagName":[]
        }
        fd['children'].forEach((tg,tgIdx)=>{
          tg['id'] = `${idx+1}_${tgIdx+1}`;
          fTemp['subTag'].push(tg['id']);
          fTemp['subTagName'].push(tg['name']);
          let tgTemp ={
          "id": tg['id'],
          "tag":tg['name'],
          "subTag":[],
          "subTagName":[]     
          }
          subF.push(tgTemp)
        })
        subF.push(fTemp)
      })
      this.currentTagDataTree_Redata = {
        fields:fileds,
        subF:subF
      }
      this.drawtagTree();
    },
    currentTagData(val) {
      this.currentTagDataTree = tools.deepClone(val['tree']);
      this.$bus.$emit("currentTagData", val);
    },
    tagsData(val) {
      const _this = this;
      let tableData = []
      val.forEach((element, index) => {
        let temp = {
          id: element['id'],
          sort: index + 1,
          name: element['fields'],
          num: element['fields'].length,
          isChoose: element['isChoose'],
        }
        if (element['isChoose']) {
          _this.chooseTagsId = element['id'];
          this.currentTagData = element;
        }
        tableData.push(temp)
      });
      this.tableData = tableData;
    },
  },
  methods: {
    
    traverseTree(idx,preId,data) {//遍历树修正id
      data = tools.deepClone(data);
      let pId = data.id;
        console.log(11133331,typeof(pId),pId,typeof(pId)=="undefined")
      if(typeof(pId)=="undefined"){
        console.log(1111,pId)
        pId = -1;
      }
      if (idx != -1) {
        data.id = `${preId}_${idx}`;
      }
      if(preId==-1){
        data.id = `${idx}`;
      }
      pId = data.id;
      console.log(idx,preId,pId,data.id);
      if (!data) return;
      let children = data['children'];
      let reC = []
      for (let i = 0; i < children.length; i++) {
        reC.push(this.traverseTree(i, pId, children[i]));
      }
      data['children'] = reC;
      return data;
    },
    click_Ent(time) {
      this.$emit("timeDur", time);
    },
    returnHome() {
      this.tableShow = true;
      this.editShow = false;
    },
    confirm(){
      const _this = this;
      console.log([_this.currentTagData,_this.currentTagDataTree_Redata,_this.currentTagDataTree])
      this.$http
        .post("/api/file/saveTag", {
          params: {
            cId:_this.currentFile['id'],
            tags: _this.currentFileTag,
            tagsData:[_this.currentTagData,_this.currentTagDataTree_Redata,_this.currentTagDataTree]
          }
        }, {})
        .then((response) => {
          _this.$message({
            message: '保存成功',
            type: 'success',
            duration: 1000
          });
        });
    },
    ModifyChooseTag(cId) {
      const _this = this;
      this.$http
        .post("/api/tag/modifyChooseState", {
          params: {
            cId: cId
          }
        }, {})
        .then((response) => {
          _this.$message({
            message: '设置成功',
            type: 'success',
            duration: 1000
          });
          _this.getTagData();
        });
    },
    handleChoose(index, row) {
      let cId = row['id'];
      this.currentTagData = this.tagsData.find((d) => { return d['id'] = cId; });
      this.ModifyChooseTag(cId);
    },
    handleEdit(index, row) {
      this.tableShow = false;
      this.editShow = true;
    },
    handleDelete(index, row) {
    },
    tableRowClassName({ row, rowIndex }) {
      if (row.isChoose) {
        return 'choose-row';
      }
      return '';
    },
    getTagData: function () {
      const _this = this;
      this.$http
        .get("/api/tag/getData", { params: {} }, {})
        .then((response) => {
          var tags = response.body;
          _this.tagsData = tags;
          
      
          // }
        });
    },
    addTreeNode(tId,newNode){
      const _this = this;
      let idLay = tId.split("_");
      let lay = idLay.length;
      let currentTagDataTree = tools.deepClone(_this.currentTagDataTree);
      let rTag = currentTagDataTree ;
      let cLay = 0;
      let cId = idLay[0];
      while (cLay < lay){
        rTag = rTag['children'].find((t) => { return t['id'] == cId; });
        console.log(rTag,cId,tId);
        cLay++;
        if(cLay < lay)
          cId =`${cId}_${idLay[cLay]}`;
      }
      let cChildrenLen = rTag['children'].length;
      newNode['id'] = `${cId}_${cChildrenLen}`;
      rTag['children'] = [...rTag['children'],newNode]
      console.log(rTag,cChildrenLen,newNode,cId,cChildrenLen)
      _this.currentTagDataTree = currentTagDataTree;
    },
    findTreeNode(tId){
      const _this = this;
      let idLay = tId.split("_");
      let lay = idLay.length;
      let currentTagDataTree = tools.deepClone(_this.currentTagDataTree);
      let rTag = currentTagDataTree ;
      let cLay = 0;
      let cId = idLay[0];
      while (cLay < lay){
        rTag = rTag['children'].find((t) => { return t['id'] == cId; });
        console.log(rTag,cId,tId);
        cLay++;
        if(cLay < lay)
          cId =`${cId}_${idLay[cLay]}`;
      }
      return rTag;
    },
    delTreeNode(tId){
      const _this  =this;
      // if((_this.newTagIds.indexOf(d.data.id) != -1)){
      let idx = _this.currentFileTag.indexOf(tId);
      if (idx != -1) {
        _this.currentFileTag.splice(idx, 1)
      }
      let idLay = tId.split("_");
      let lay = idLay.length;
      let currentTagDataTree = tools.deepClone(_this.currentTagDataTree);

      let rTag = currentTagDataTree ;
      let cLay = 0;
      let cId = idLay[0];
      while (cLay < lay-1){
        rTag = rTag['children'].find((t) => { return t['id'] == cId; });
        cLay++;
        if(cLay < lay)
          cId =`${cId}_${idLay[cLay]}`;
      }
      console.log(rTag,cId,tId);
      // let rTag;
      // if (lay == 1) {
      //   rTag = currentTagDataTree;
      // }
      // else { rTag = currentTagDataTree['children'].find((t) => { return t['id'] == rId[lay - 2]; }); }
      // if (rId.length > 1) {
      rTag['children'] = rTag['children'].filter(function (obj) {
        return obj.id !== tId;
      });
      // }
      _this.currentTagDataTree = currentTagDataTree;
    },
    modTreeNodeName(tId,newName){
      const _this = this;
      let idLay = tId.split("_");
      let lay = idLay.length;
      let currentTagDataTree = tools.deepClone(_this.currentTagDataTree);
      let rTag = currentTagDataTree ;
      let cLay = 0;
      let cId = idLay[0];
      while (cLay < lay){
        rTag = rTag['children'].find((t) => { return t['id'] == cId; });
        console.log(rTag,cId,tId);
        cLay++;
        if(cLay < lay)
          cId =`${cId}_${idLay[cLay]}`;
      }
      rTag['name'] =newName;
      _this.currentTagDataTree = currentTagDataTree;
    },
    drawtagTree() {
      const _this = this;
      let width = this.$refs.tagTree.offsetWidth;
      let height = this.$refs.tagTree.offsetHeight;
      let color = _this.mcolor;
      let colorMap = _this.colorMap;
      // var tree = d3.tree()
      //   .size([width, height - 200]);
      d3.select("#tagTree").select("svg").remove();
      var svg = d3.select("#tagTree").append("svg")
        .attr("width", width)
        .attr("height", height);

      let treeGTransformX = _this.treeGTransformX;
      let treeGTransformY = _this.treeGTransformY;
      let treeGTransformK = _this.treeGTransformK;

      let groups = svg.append("g")
        .attr("id", "edittagTreeg")
        .attr("width", width)
        .attr("height", height)
        .attr("transform",  "translate("+treeGTransformX+',' +treeGTransformY + ") scale("+treeGTransformK+")");

      let stx = 0;
      let sty = 0;
      let stk = 1;
      var graphZoom = d3.zoom()
        .scaleExtent([0, 10])
        .on("start", (e) => {
          sty = e.transform.y;
          stx = e.transform.x;
          stk = e.transform.k;
        })
        .on('zoom', (e) => {
          treeGTransformX = _this.treeGTransformX + e.transform.x - stx;
          treeGTransformY = _this.treeGTransformY + e.transform.y - sty;
          treeGTransformK = _this.treeGTransformK + e.transform.k - stk;
          groups.attr('transform', 'translate(' + (treeGTransformX) + ',' + (treeGTransformY) + ') scale(' + (treeGTransformK) + ')')
        })
        .on('end', (e) => {
          _this.treeGTransformX = treeGTransformX;
          _this.treeGTransformY = treeGTransformY;
          _this.treeGTransformK = treeGTransformK;
          groups.attr('transform', 'translate(' + (treeGTransformX) + ',' + (treeGTransformY) + ') scale(' + (treeGTransformK) + ')')
        });
        // .on('zoom', (e) => {
        //   groups.attr('transform', e.transform)
        // })
      svg.call(graphZoom)

      const gLink = groups.append("g")
        .attr("fill", "none")
        .attr("stroke", "#555")
        .attr("stroke-opacity", 0.4)
        .attr("stroke-width", 1.5);

      const gNode = groups.append("g")
        .attr("cursor", "pointer")
        .attr("pointer-events", "all")

      let data = this.currentTagDataTree;
      let diagonal = d3.linkHorizontal().x(d => d.y).y(d => d.x);
      let tree = d3.tree().nodeSize([35, 200])//.size([height, width - 80]);//.size([(height - margin.left - margin.right) * 2, (width - margin.left - margin.right)-10])
      const root = d3.hierarchy(data);
      root.descendants().forEach((d, i) => {
        d.id = i;
        d._children = d.children;
        //if (d.depth && d.data.name.length !== 2) d.children = null; //当前条件下的节点不自动展示
      });
      function update(source) {
        const duration = 0//d3.event && d3.event.altKey ? 2500 : 250;
        const nodes = root.descendants().reverse();
        const links = root.links();
        tree(root);

        const node = gNode.selectAll("g")
          .data(nodes, d => d.id);
        let left = root;
        let right = root;
        root.eachBefore(node => {
          if (node.x < left.x) left = node;
          if (node.x > right.x) right = node;
        });


        const height = right.x - left.x;


        const transition = svg.transition()
          .duration(duration)
          // .attr("viewBox", [0, left.x, width, height])
          .tween("resize", window.ResizeObserver ? null : () => () => svg.dispatch("toggle"));


        const nodeEnter = node.data(nodes).enter().append("g")
          .attr("id", d => `nodeEnter_${d.data.id}`)
          .attr("transform", (d) => {
            return `translate(${d.y - 80},${d.x})`
          })
        // .on("click", (event, d) => {
        //   d.children = d.children ? null : d._children;
        //   update(d);
        // })  

        nodeEnter.append("text")
          .attr("id", d => `tagText_${d.data.name}`)
          .attr("dy", "0.31em")
          .text(d => d.data.name)


        nodeEnter.append("rect")
          .attr("id", d => `tagRect_${d.data.name}`)
          .attr("y", '-14')
          .attr("x", '-4')
          .attr("height", 28)
          .attr("rx", 2)
          .attr("width", d => {
            let textW = document.getElementById(`tagText_${d.data.name}`).getBBox().width+8
            return textW>50?textW:50;
          })
          .attr("fill", function (d) {
            let idx = _this.currentFileTag.indexOf(d.data.id)
            if ((idx != -1)||(_this.newTagIds.indexOf(d.data.id) != -1)) {
              return _this.mcolor[d.data.id.split("_")[0]];
            }
            return 'grey'
          })
          .attr("opacity", (d)=>{
            if ((_this.newTagIds.indexOf(d.data.id) != -1)) {
              return 0.5;
            }
            return 1;
          })
          .attr("stroke-dasharray", (d)=>{
            if ((_this.newTagIds.indexOf(d.data.id) != -1)) {
              return "5,10";
            }
            return 0;
          })
          .attr("stroke", "rgb(100,100,100)")
          .attr("stroke-width", 2)
          // .on("mouseleave", function (e,d) {
          //     d3.selectAll(`.tagBut`)
          //     .attr("opacity", 0)
          // })
          .on("mousedown", function (e,d) {//修改
              d3.selectAll(`.tagBut`)
              .attr("opacity", 0)
              var input = d3.select(`#nodeEnter_${d.data.id}`).append("foreignObject")
              .attr("id","tagNameInput")
              .attr("y", '-14')
              .attr("x", '-4')
              .attr("height", 28)
              .attr("width", d3.select(this).attr("width"))
              .append("xhtml:body")
              .append("input")
              .attr("type", "text");

              document.getElementById('tagNameInput').addEventListener('keydown', function (event) {
                if("Enter" == event.key){
                  let tId = d.data.id;
                  _this.modTreeNodeName(tId,event.target.value)
                  d3.select(`#nodeEnter_${tId}`).select("foreignObject").remove()
                }
              });

          })
          .on("mouseover", function (e,d) {
              d3.selectAll(`.tagBut`)
              .attr("opacity", 0)
              // if((_this.newTagIds.indexOf(d.data.id) != -1)){
              d3.select(`#tagDeletBut_${d.data.id}`)
              .attr("opacity", 1)
              d3.select(`#tagAddBut_${d.data.id}`)
              .attr("opacity", 1)
              d3.select(`#tagChooseBut_${d.data.id}`)
              .attr("opacity", 1)
              d3.select(`#tagMergeBut_${d.data.id}`)
              .attr("opacity", 1)
            // }
          })

        nodeEnter.append("rect")//合并
          .attr("id", d => `tagMergeBut_${d.data.id}`)
          .attr("class",`tagBut`)
          .attr("y", '-10')
          .attr("x", d => {
            return document.getElementById(`tagRect_${d.data.name}`).getBBox().width+80;
          })
          .attr("opacity", 0)
          .attr("height", 20)
          .attr("rx", 2)
          .attr("width", 20)
          .attr("stroke", "black")
          .attr("fill","yellow")
          .on("mousedown", function (e,d) {
            let cId = d.data.id;
            console.log(_this.mergeSourceNodeId,_this.mergeTagrgetNodeId,cId);
            if(_this.mergeSourceNodeId == ""){
              _this.mergeSourceNodeId = cId;
            }
            else{
              if(cId != _this.mergeSourceNodeId)
              _this.mergeTagrgetNodeId = cId;
              let sNode = _this.findTreeNode(_this.mergeSourceNodeId);
              _this.delTreeNode(_this.mergeSourceNodeId);
              _this.addTreeNode(_this.mergeTagrgetNodeId,sNode);
              _this.mergeSourceNodeId = "";
              _this.mergeTagrgetNodeId = "";
            }
            })        

        nodeEnter.append("rect")//选中
          .attr("id", d => `tagChooseBut_${d.data.id}`)
          .attr("class",`tagBut`)
          .attr("y", '-10')
          .attr("x", d => {
            return document.getElementById(`tagRect_${d.data.name}`).getBBox().width+8;
          })
          .attr("opacity", 0)
          .attr("height", 20)
          .attr("rx", 2)
          .attr("width", 20)
          .attr("stroke", "black")
          .attr("fill",d=>{
            let idx = _this.currentFileTag.indexOf(d.data.id)
            if ((idx != -1)||(_this.newTagIds.indexOf(d.data.id) != -1)) {
              return "green"
            }
            return 'white'
          })
          .on("mousedown", function (e,d) {
            let tId = d.data.id;
              let idx = _this.currentFileTag.indexOf(tId);
              if(idx == -1){
                _this.currentFileTag.push(tId)
              }
              else{
                _this.currentFileTag.splice(idx, 1)
              }
            })        

        nodeEnter.append("rect")//添加
          .attr("id", d => `tagAddBut_${d.data.id}`)
          .attr("class",`tagBut`)
          .attr("y", '-10')
          .attr("x", d => {
            return document.getElementById(`tagRect_${d.data.name}`).getBBox().width+56;
          })
          .attr("opacity", 0)
          .attr("height", 20)
          .attr("stroke", "black")
          .attr("rx", 2)
          .attr("width", 20)
          .attr("fill","blue")
          .on("mousedown", function (e, d) {
            let tId = d.data.id;
            let newTreeNode = {
              "id":"",
              "name":"",
              "children":[]
            }
            _this.addTreeNode(tId,newTreeNode);
          })
            
        nodeEnter.append("rect")//删除
          .attr("id", d => `tagDeletBut_${d.data.id}`)
          .attr("class",`tagBut`)
          .attr("y", '-10')
          .attr("x", d => {
            return document.getElementById(`tagRect_${d.data.name}`).getBBox().width+32;
          })
          .attr("opacity", 0)
          .attr("height", 20)
          .attr("rx", 2)
          .attr("width", 20)
          .attr("stroke", "black")
          .attr("fill","red")
          .on("mousedown", function (e,d) {
              let tId = d.data.id;
              _this.delTreeNode(tId);
            // }
              // d.children = d.children ? null : d._children;
              // update(d);
            })

        nodeEnter.append("text")
          .attr("dy", "0.31em")
          .attr("x", d => d._children ? 0 : 0)
          .attr("fill", "white")
          .on("mouseover", function (e,d) {
          //   d3.selectAll(`.tagDeletBut`)
          //   .attr("opacity", 0)
          //   if((_this.newTagIds.indexOf(d.data.id) != -1)){
          //   d3.select(`#tagDeletBut_${d.data.id}`)
          //   .attr("opacity", 1)
          // }
          })
          .on("mousedown", function (e,d) {
              let tId = d.data.id;
              let idx = _this.currentFileTag.indexOf(tId);
          
              if(idx == -1){
                _this.currentFileTag.push(tId)
              }
              else{
                _this.currentFileTag.splice(idx, 1)
              }
              // d.children = d.children ? null : d._children;
              // update(d);
            })
          .attr("text-anchor", d => d._children ? "start" : "start")
          .text(d => d.data.name)
          .clone(true).lower()
          .attr("stroke-linejoin", "round")
          .attr("stroke-width", 3)
          .attr("stroke", "white");
        // nodeEnter.append("circle")
        //   .attr("r", 10)
        //   .attr("fill", function (d) {
        //     return 'grey'
        //   })
        //   .attr("stroke", "rgb(100,100,100)")
        //   .attr("stroke-width", 1)
        //   .on("mouseover", function () {
        //     d3.select(this).attr("r", 15);

        //   })
        //   .on("mouseleave", function () {
        //     d3.select(this).attr("r", 10)
        //   })
        // .on("mousedown", function () {
        //   _this.click_node();
        // })



        const link = gLink.selectAll("path")
          .data(links, d => d.target.id);

        const linkEnter = link.enter().append("path")
          .attr("d", d => {
            const o = { x: d.source.x, y: d.source.y };
            const p = { x: d.target.x, y: d.target.y }
            return diagonal({ source: o, target: p });
          })
          .attr("stroke", d=>{
            if(_this.newTagIds.indexOf(d.target.data.id) == -1){

            return "rgb(100,100,100)"
            }
              return "rgb(200,200,200)"
          })
          .attr("stroke-width", 2)
        const nodeUpdate = node.merge(nodeEnter).transition(transition)
          .attr("transform", d => `translate(${d.y},${d.x})`)
          .attr("fill-opacity", 1)
          .attr("stroke-opacity", 1);
        // Transition exiting nodes to the parent's new position.
        const nodeExit = node.exit().transition(transition).remove()
          .attr("transform", d => `translate(${source.y},${source.x})`)
          .attr("fill-opacity", 0)
          .attr("stroke-opacity", 0);


        // Transition links to their new position.
        link.merge(linkEnter).transition(transition)
        .attr("d", d => {
            const o = { x: d.source.x, y: d.source.y+100 };
            const p = { x: d.target.x, y: d.target.y }
            return diagonal({ source: o, target: p });
          }).attr("opacity", 1)
        // Transition exiting nodes to the parent's new position.
        link.exit().transition(transition).remove()
          .attr("d", d => {
            const o = { x: source.x, y: source.y };
            return diagonal({ source: o, target: o });
          }).attr("opacity", 0);


        // Stash the old positions for transition.
        root.eachBefore(d => {
          d.x0 = d.x;
          d.y0 = d.y;
        });


      }
      update(root)
    },
  },
  created() {
    const _this = this;
    this.getTagData();
    this.$nextTick(() => {
    });
  },
  mounted() {
    const _this = this;
    
    this.$bus.$emit("tagEdit","true");
    this.$bus.$on('tagEdit', (val) => {
      if(val == 'true'){
        this.$nextTick(() => {
            this.drawtagTree();
        });
      }
    });
    this.$bus.$on('LLMPreTags', (val) => {
      _this.LLMPreTags = val;
    });
    this.$bus.$on('currentFile', (val) => {
      _this.currentFile = val;
    });
  },
  // beforeDestroy() {
  //   clearInterval(this.moveTimer);
  // },
} 
</script>

<style>
@import './index.css';
</style>
