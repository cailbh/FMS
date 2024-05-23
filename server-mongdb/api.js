/* eslint-disable no-unused-vars */
"use strict";
const models = require('./db');
const express = require('express');
const router = express.Router();

const child_process = require('child_process');
const iconv = require('iconv-lite');

// / 引入文件模块 
const fs = require("fs");
var encoding = 'cp936';
var binaryEncoding = 'binary';
// 获取具体文件
router.get('/api/file/getDoc', (req, res) => {
    let fileName = req.query.fileName;
    // 假设我们的word文档文件就存放在这个doc目录里面
    let docxUrl = `D:/Work/YanCao/jg/fileData/${fileName}.docx`
  
    // 允许跨域
    res.header("Access-Control-Allow-Origin", "*");
  
    // 设置请求头
    res.writeHead(200, {
      // 指定文件类型为docx
      'Content-Type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document;charset=utf-8',
    })
  
    //创建可读流
    let readStream = fs.createReadStream(docxUrl,{encoding: null})// 默认null})
    // 将读取的结果以管道pipe流的方式返回给前端
    readStream.pipe(res);
  
  })

// 打标
router.post('/api/tag/AutoMarking', (req, res) => {
    let fileId = req.body.params.cId;
    let indexStr =` ${fileId} 2`;
    console.log(`python ../public/py/AutoMarking.py ${indexStr}`)
    process.env.LANG ='zh_CN.GBK';
    var workerProcess = child_process.exec(`conda activate LLM &&  python ../public/py/AutoMarking.py ${indexStr}`,{ encoding: 'buffer' }, function (error, stdout, stderr) {
        if (error) {
            console.log(error.stack);
            console.log('Error code: '+error.code);
            console.log('Signal received: '+error.signal);
        }else{
        //   console.log('stdout: ' + stdout);
        //   console.log('stderr: ' + stderr);

        console.log(iconv.decode(stdout, 'cp936'));
        //   res.send(stdout);
          res.send(eval("(" + (iconv.decode(stdout, 'cp936')).replace(/\n/g,'') + ")"))   //这里要eval一下，然后在客户端才能eval将字符串转化为json数组
        }
        
          
      });
    
      workerProcess.on('exit', function (code) {
          console.log('子进程已退出，退出码 '+code);
      });
    // res.send('{"技术领域": ["人工智能", "数据安全", "能源管理"],"关键技术": ["异构资源调度", "GPU自动适配", "RDMA网络技术", "算力管理优化", "AI任务切分与调度"]}')
  })
// 获取文件列表数据
router.get('/api/file/getData', (req, res) => {
    // 通过模型去查找数据库
    models.File.find((err, data) => {
        if (err) {
            res.send(err);
        } else {

            res.send(data);
        }
    });
});

// 获取标签数据
router.get('/api/tag/getData', (req, res) => {
    // 通过模型去查找数据库
    models.Tag.find((err, data) => {
        if (err) {
            res.send(err);
        } else {

            res.send(data);
        }
    });
});
//保存标签
router.post('/api/file/saveTag', (req, res) => {
    let cId = req.body.params.cId;
    let tags = req.body.params.tags;
    let tagsData = req.body.params.tagsData;
    let tagsO = tagsData[0];
    let tagsN = tagsData[1];
    let treeN = tagsData[2];
    // tagsO['subF'] = tagsN['subF'];
    // tagsO['fields'] = tagsN['fields'];
    // tagsO['tree'] =treeN;
    console.log(tagsO);
    models.File.updateOne({ id: cId }, { $set: { tags: tags} }).then(result => {
        models.Tag.updateOne({ id: tagsO['id'] }, { $set: { subF: tagsN['subF'], fields: tagsN['fields'], tree: treeN} }).then(result =>
            res.send('createRelsuccessed2')
        ).catch(error => {
            console.error('更新时发生错误:', error);
            res.send(error)
        });//
    }
    ).catch(error => {
        console.error('更新时发生错误:', error);
        res.send(error)
    });
});
//修改标签选中
router.post('/api/tag/modifyChooseState', (req, res) => {
    let cId = req.body.params.cId;
    models.Tag.updateOne({ isChoose: true }, { $set: { isChoose: false } }).then(result => {
        models.Tag.updateOne({ id: cId }, { $set: { isChoose: true } }).then(result =>
            res.send('createRelsuccessed2')
        ).catch(error => {
            console.error('更新时发生错误:', error);
            res.send(error)
        });//
    }
    ).catch(error => {
        console.error('更新时发生错误:', error);
        res.send(error)
    });
});
module.exports = router;