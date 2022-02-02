'use strict';
var express = require('express');
var router = express.Router();
var neo4j = require('neo4j-driver');
var fs = require('fs');
// var {spawn} = require('child_process');
const spawn = require("child_process").spawnSync;
const mydata = JSON.parse(fs.readFileSync('routes/Queries.json'));
const dbInfo = JSON.parse(fs.readFileSync('routes/cfr/all.json'));
var domain;
var cutset;

var driver;
var path_info = [];
var banned_sent = "";
var credentials = {
  username: '',
  password: ''
};
var result_obj;

function _neo4jToSigmaNode(node) {
  var sNode = {
    // id: node.identity['low'].toString(),
    labels: node.labels[1],
    properties: node.properties,
    x: Math.random(),
    y: Math.random(),
    size: 0.5,
    color: "orange",
    label: node.properties['name'],
    labelSizeRatio: 0.5,
    // icon: {
    //   name: 'f007', // Fontawesome unicode
    //   color: '#FFF', // Color of the font
    //   scale: 1.0 // Scale ratio
    // }
    image: {
      url: "../public/images/group.png",
      scale: 1,
      clip: 0.85
    }
  };

  if (node.hasOwnProperty("identity")) {
    sNode.id = node.identity['low'].toString();
  } else {
    sNode.id = node.id.toString();
  }

  if(sNode.labels === "User") {
    sNode.color = "green";
  } else if(sNode.labels === "Computer") {
    sNode.color = "orange";
  } else if(sNode.labels === "Group") {
    sNode.color = "yellow";
  } else if(sNode.labels === "OU") {
    sNode.color = "blue";
  } else if(sNode.labels === "Domain") {
    sNode.color = "red";
  } else {
    sNode.color = "purple";
  }

  // Look if there is a defined style for labels


  return sNode;
}

function _neo4jToSigmaEdge(edge) {
  var sEdge = {
    // id: edge.identity.toString(),
    // rel_type: edge.type,
    // source: edge.start.toString(),
    // target: edge.end.toString(),
    // properties: edge.properties,
    size: 1,
    color: "#000",
    // label: edge.type,
    type: "arrow"
  };

  if (edge.hasOwnProperty("identity")) {
    sEdge.id = edge.identity.toString();
    sEdge.source = edge.start.toString();
    sEdge.target = edge.end.toString();
  } else {
    sEdge.id = edge.id.toString();
    sEdge.source = edge.start.id.toString();
    sEdge.target = edge.end.id.toString();
  }


  if (edge.hasOwnProperty("label")) {
    sEdge.rel_type = edge.label;
    sEdge.label = edge.label;
  } else {
    sEdge.rel_type = edge.type;
    sEdge.label = edge.type;
  }

  if (edge.hasOwnProperty("properties")) {
    sEdge.properties = edge.properties;

  }

  // Look if there is a defined style for the edge type

  return sEdge;
}

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: 'Express' });
});


router.get('/login', async function(req, res, next) {
  console.log("Login start");
  const params = req.query;
  console.log(params.username);
  console.log(params.password);
  driver = neo4j.driver('bolt://localhost', neo4j.auth.basic(params.username, params.password));
  console.log("Login driver creating");
  try {
    await driver.verifyConnectivity();
    console.log('Driver created');
    credentials.username = params.username;
    credentials.password = params.password;
  } catch (error) {
    console.log(`connectivity verification failed. ${error}`);
    res.sendStatus(500);
  }
  console.log(credentials)
  res.send("go");
});

router.get('/get_domain', async function(req, res, next) {
  var index = parseInt(req.query.indexs);
  var session = driver.session();
  var params = {};
  // var query = "MATCH (n) WHERE n.name =~ '(?i)DOMAIN.*' RETURN n limit 2";
  var query = `MATCH (n) WHERE n.name =~ '(?i)DOMAIN ADMINS@.*' RETURN n`
  const final = await session.run(query)
  .then(
    function(result) {
      return result;
    });
  session.close();
  // path_info =[];
  console.log(final);
  domain = final.records[0]._fields[0].properties.domain;
  let objectID = final.records[0]._fields[0].properties.objectid;
  let identity_domain = final.records[0]._fields[0].identity['low'].toString();
  result_obj = {
    domain_name: domain,
    objectID: objectID,
    id_domain: identity_domain
  };
  console.log(result_obj);
  res.json(result_obj);

});

router.get('/get_path_now', async function(req, res, next) {
  var index;
  if (req.query.hasOwnProperty('indexs')) {
    index = parseInt(req.query.indexs);
  }
  var session = driver.session();
  var query, option;
  var params = {};
  if (req.query.hasOwnProperty('option')) {
    //path_info
    option = parseInt(req.query.option);
    query = mydata[index].queryList[1].query;
    params = {result: path_info[option]};
  } else if (req.query.hasOwnProperty('raw_query')) {
    query = req.query.raw_query;
  } else {
    //no path_info
    query = mydata[index].queryList[0].query;
    params = mydata[index].queryList[0].props;
  }
  const final = await session.run(query, params)
    .then(
      function(result) {
        // empty graph object
        let graph = { nodes: [], edges: [] };
        let nodesAlreadyProcess = [];
        let edgesAlreadyProcess = [];
        console.log(result);
        // for each rows
        result.records.forEach(record => {
          // for each column
          // if (count === true) {
            // console.log(record);
          //   count = false;
          // }
          record.forEach((value, key) => {
            // console.log(value);
            // if it's a node
            if (value && value.hasOwnProperty("labels")) {
              if (
                nodesAlreadyProcess.indexOf(value.identity.toString()) ===
                -1
              ) {
                graph.nodes.push(_neo4jToSigmaNode(value));
                nodesAlreadyProcess.push(value.identity.toString());
              }
            }

            // if it's an edge
            if (value && value.hasOwnProperty("type")) {
              if (
                edgesAlreadyProcess.indexOf(value.identity.toString()) ===
                -1
              ) {
                graph.edges.push(_neo4jToSigmaEdge(value));
                edgesAlreadyProcess.push(value.identity.toString());
              }
            }

            // if it's a path
            if (value && value.hasOwnProperty("segments")) {
              // console.log(value.segments);
              value.segments.forEach(seg => {
                // console.log(seg);
                if (
                  nodesAlreadyProcess.indexOf(
                    seg.start.identity.toString()
                  ) === -1
                ) {
                  graph.nodes.push(_neo4jToSigmaNode(seg.start));
                  nodesAlreadyProcess.push(seg.start.identity.toString());
                }
                if (
                  nodesAlreadyProcess.indexOf(
                    seg.end.identity.toString()
                  ) === -1
                ) {
                  graph.nodes.push(_neo4jToSigmaNode(seg.end));
                  nodesAlreadyProcess.push(seg.end.identity.toString());
                }

                  if (
                    edgesAlreadyProcess.indexOf(seg.relationship.identity.toString()) ===
                    -1
                  ) {
                    graph.edges.push(_neo4jToSigmaEdge(seg.relationship));
                    edgesAlreadyProcess.push(seg.relationship.identity.toString());
                  }


              });
            }
          });
        });

        return graph;
      })
    .catch(function (error) {
      res.sendStatus(500);
    });
  res.json(final);

});

router.get('/get_path_info', async function(req, res, next) {
  var index = parseInt(req.query.indexs);
  var session = driver.session();
  var params = {};
  var query = mydata[index].queryList[0].query;
  params = mydata[index].queryList[0].props;
  const final = await session.run(query, params)
  .then(
    function(result) {
      return result;
    });
  session.close();
  path_info =[];
  path_info = final.records[0]._fields;
  res.send(path_info) ;

});

router.get('/ransomulator', function(req, res, next) {
  //run file ransomulator.py
  const params = req.query;
  let path = "routes/Ransomulator/ransomulator.py";
  var python;
  if (params.simulate !== "practical") {
    python = spawn('python', [path, '-s', params.simulate]);
  } else {
    python = spawn('python', [path]);
  }

  //read the output file conversion.json
  let rawdata = fs.readFileSync('routes/Ransomulator/conversion4.json');

  let data = JSON.parse(rawdata);
  console.log(data);
  res.send(JSON.stringify(data));
});

router.get('/shothound', function(req, res, next) {
  const params = req.query;
  let path = 'routes/ShotHound/shothound.py';
  var python;
  if (params.source !== "" && params.target !== "" ) {
    python = spawn('python', [path, credentials.username, credentials.password, domain, '-s', params.source, 't', params.target]);
  } else if (params.source !== "") {
    python = spawn('python', [path, credentials.username, credentials.password, domain, '-s', params.source]);
  } else if (params.target !== "") {
    python = spawn('python', [path, credentials.username, credentials.password, domain, '-t', params.target]);
  } else {
    python = spawn('python', [path, credentials.username, credentials.password, domain]);
  }
  // ,"-s " + params.source, "-t " + params.target
  // console.log('stdout here: \n' + python.stdout);
  //read the output file conversion.json
  let rawdata = fs.readFileSync('routes/ShotHound/sample.json');
  let rawdata2 = fs.readFileSync('routes/ShotHound/finalInfo.json');
  let data = JSON.parse(rawdata);
  let data2 = JSON.parse(rawdata2);
  let data_sent = [
    data, data2
  ];
  console.log(data_sent);
  res.send(JSON.stringify(data_sent));

  // console.log(mydata);

});

router.get('/iterative_cut', function(req, res, next) {
  //run file
  var python_cut;
  var params = req.query;
  var banned_iterator = params.bannedSet.split(',');
  let path = "routes/iterative_cut/iterative_cut.py";

  if (params.bannedSet === "") {
    banned_sent = "";
    python_cut = spawn('python', [path, result_obj.objectID, '-1']);
    // console.log(python_cut)
  } else {
    banned_iterator.forEach(item => {
      banned_sent += "(";
      banned_sent += cutset[item][0];
      banned_sent += ",";
      banned_sent += cutset[item][1];
      banned_sent += ")";
    });
    console.log(banned_sent);
    python_cut = spawn('python', [path, result_obj.objectID, banned_sent]);
  }

  //read the output file conversion.json
  let rawdata = fs.readFileSync('routes/iterative_cut/cutset.json');

  let data = JSON.parse(rawdata);
  // cutset = Object.keys(data).forEach(function(key) {
  //   let source = dbInfo.nodes.find(node => node.properties.objectid === data[key][0]);
  //   let dest = dbInfo.nodes.find(node => node.properties.objectid === data[key][1]);
  //   data[key][0] = source.properties.name;
  //   data[key][1] = dest.properties.name;

  // });
  cutset = data;
  // dbInfo.nodes.find(node => node.id.toString() === item[i].toString());
  // console.log(data);
  res.send(JSON.stringify(data));
});

router.get('/regret_matching', function(req, res, next) {
  const params = req.query;
  let path = "routes/cfr/cfr_check.py";
  var python = spawn('python', [path, params.source, params.target]);

  // read the output file conversion.json
  let rawdata = fs.readFileSync('routes/cfr/cfr_check.json');

  let data = JSON.parse(rawdata);
  let nodesAlreadyProcess = [];
  let graph = { nodes: [], edges: {} };

  for (var key in data) {
    var item = data[key];
    graph.edges[key] = []
    for(var i=0; i<item.length - 1; i++) {
      // var result = jsObjects.find(obj => {
      //   return obj.b === 6
      // })
      var source = dbInfo.nodes.find(node => node.id.toString() === item[i].toString());
      var dest = dbInfo.nodes.find(node => node.id.toString() === item[i+1].toString());
      if (
        nodesAlreadyProcess.indexOf(
          item[i].toString()
        ) === -1
      ) {
        graph.nodes.push(_neo4jToSigmaNode(source));
        nodesAlreadyProcess.push(item[i].toString());
      }

      if (
        nodesAlreadyProcess.indexOf(
          item[i+1].toString()
        ) === -1
      ) {
        graph.nodes.push(_neo4jToSigmaNode(dest));
        nodesAlreadyProcess.push(item[i+1].toString());
      }

      var _edge = dbInfo.edges.find(
        edge => edge.start.id.toString() === item[i].toString() && edge.end.id.toString() === item[i+1].toString()
      );

      graph.edges[key].push(_neo4jToSigmaEdge(_edge));

    }
  }

  res.json(graph);
  // console.log(data);
  // res.send(JSON.stringify(data));
});
var edge_id = 0;
router.get('/regret_matching_v2', function(req, res, next) {
  const params = req.query;
  let path = "routes/cfr/cfr_check_2.py";
  var python = spawn('python', [path, params.source, params.target]);

  // read the output file conversion.json
  let rawdata = fs.readFileSync('routes/cfr/cfr_check.json');

  let data = JSON.parse(rawdata);
  console.log(data);
  let nodesAlreadyProcess = [];
  let edgesAlreadyProcess = [];
  let graph = { nodes: [], edges: {} };
  for (var key in data) {
    var item = data[key];
    graph.edges[key] = []
    for(var i=0; i<item.length - 1; i++) {
      if (
        nodesAlreadyProcess.indexOf(
          item[i].toString()
        ) === -1
      ) {
        let node = {
          id: item[i],
          labels: item[i],
          x: Math.random(),
          y: Math.random(),
          size: 0.5,
          color: "orange",
          label: item[i],
          labelSizeRatio: 0.5,
        }
        graph.nodes.push(node);
        nodesAlreadyProcess.push(item[i].toString());
      }

      if (
        nodesAlreadyProcess.indexOf(
          item[i+1].toString()
        ) === -1
      ) {
        let node = {
          id: item[i+1],
          labels: item[i+1],
          x: Math.random(),
          y: Math.random(),
          size: 0.5,
          color: "orange",
          label: item[i+1],
          labelSizeRatio: 0.5,
        }
        graph.nodes.push(node);
        nodesAlreadyProcess.push(item[i+1].toString());
      }

      let edge = {
        id: edge_id,
        size: 1,
        color: "#000",
        type: "line",
        source: item[i],
        target: item[i+1]
      }
      if (!edgesAlreadyProcess.some(obj => obj.source === item[i] && obj.target === item[i+1])) {
        graph.edges[key].push(edge);
        edge_id++;
      } else {
        graph.edges[key].push(edgesAlreadyProcess.some(obj => obj.source === item[i] && obj.target === item[i+1]));
      }

    }
  }
  console.log(nodesAlreadyProcess);
  console.log(graph);

  res.json(graph);
});

router.get('/aaai', function(req, res, next) {
  const params = req.query;
  let path = 'routes/aaai/driver.py';
  var python = spawn('python', [path, params.budget, params.start]);

  //read the output file conversion.json
  let rawdata = fs.readFileSync('routes/aaai/best_methods.json');
  let data = JSON.parse(rawdata);
  console.log(data);
  res.send(JSON.stringify(data));

  // console.log(mydata);

});


module.exports = router;
// "MATCH (n)-[r]->(m) RETURN n,r,m LIMIT $limit", {limit:50}"