var mydata = JSON.parse(datum);
// var database = JSON.parse(db);
var vueinst = new Vue({
    el: "#app",
    data: {
        login: {
            username: '',
            password: '',
        },
        login_fail: '',
        wave: 0,
        searcher: '',
        query_index: -1,
        selected_service: 'hello',
        loading: false,
        domain_info: {
            domain_name: 'Pending',
            id_domain: '',
            objectID: ''
        },
        // -------Ransomulator----------
        ransom_title: ["Host name", "Total"],
        ransom: [
            // {Hostname: 0, Total: 0, wave_1: 0, wave_2: 0, wave_3: 0}
        ],
        ransom_open: false,
        ransom_comp: "",
        simulate: "practical",

        //-------QUERY-BOX-------------
        query: [],
        query_box: false,
        query_options: [
            {name: 'COMP A'},
            {name: 'COMP A'},
            {name: 'COMP A'},
            {name: 'COMP A'}
        ],
        option_index: -1,
        option_ready: false,
        alert: false,

        //---------QUERIES-------------
        // -------SHOTHOUND ------------
        shothound_open: false,
        result_shothound_open: false,
        shothound_title: ["Carrier", "Target"],
        shothound: {

        },
        path: {
            "Practical path": 0,
            "Logical path": 0,
            "Percent": 0
        },
        shothound_input: {
            source: "",
            target: "",
        },
        shothound_empty: true,

        // ----------NODE INFO -------------
        props: {
        },

        node_info: false,

        // ----------NODE TYPES-----------------
        // ----------RAW QUERY------------
        raw_query: "",


        // exclude_cut: [1,2,3],

        //----------ITERATIVE CUT---------
        cuts: {
            // '0': [
            //     'S-1-5-21-3575477103-1058849377-3253337160-1001',
            //     'S-1-5-21-3575477103-1058849377-3253337160-3152'
            // ],
            // '1': [
            //     'S-1-5-21-3575477103-1058849377-3253337160-1003',
            //     'S-1-5-21-3575477103-1058849377-3253337160-3154'
            // ],
            // '2': [
            //     'S-1-5-21-3575477103-1058849377-3253337160-1005',
            //     'S-1-5-21-3575477103-1058849377-3253337160-3156'
            // ]
        },
        iterative_title: ['Number', 'Source', 'Destination'],
        iterative_open: false,
        banned_set: [],
        cut_empty: false,

        //---------REGRET MATCHING---------
        cfr: {
            source: 0,
            target: 0
        },
        path_set: {
            nodes: [],
            edges: {}
        },
        path_empty: false,
        regret_open: false,
        regret_option: 0,

        // ------------AAAI-------------
        aaai_input: {
            budget: 0,
            start: 0

        },
        aaai_open: false,
        aaai_page_order: 0,
        aaai_result: [
            // {
            //     "id": 0,
            //     "best": [
            //         "greedy",
            //         "gnn"
            //     ],
            //     "greedy": [
            //         [
            //             530,
            //             1362
            //         ],
            //         [
            //             869,
            //             48
            //         ],
            //         [
            //             869,
            //             1362
            //         ],
            //         [
            //             814,
            //             48
            //         ],
            //         [
            //             814,
            //             1362
            //         ]
            //     ],
            //     "gnn": [
            //         [
            //             530,
            //             1362
            //         ],
            //         [
            //             814,
            //             48
            //         ],
            //         [
            //             814,
            //             1362
            //         ],
            //         [
            //             869,
            //             48
            //         ],
            //         [
            //             869,
            //             1362
            //         ]
            //     ]
            // },
            // {
            //     "id": 1,
            //     "best": [
            //         "greedy",
            //         "gnn"
            //     ],
            //     "greedy": [
            //         [
            //             530,
            //             1362
            //         ],
            //         [
            //             530,
            //             1460
            //         ],
            //         [
            //             927,
            //             48
            //         ],
            //         [
            //             927,
            //             1460
            //         ],
            //         [
            //             1362,
            //             48
            //         ]
            //     ],
            //     "gnn": [
            //         [
            //             530,
            //             1362
            //         ]
            //     ]
            // }
        ]

    },

    filters: {
        uppercase: function(v) {
          return v.toUpperCase();
        },

        toNumber: function(v) {
            return parseInt(v);
        }
    },

    methods: {
        get_wave: function() {
            var xhttp = new XMLHttpRequest();
            var _this = this;
            xhttp.onreadystatechange = function() {
                // if (this.readyState == 4 && this.status == 200) {
                //     var result=JSON.parse(this.responseText);
                //     _this.wave = result.low;
                // }
            };
            xhttp.open("GET", "/get_wave", true);
            xhttp.send();
        },

        set_index: function(i) {
            this.query_index = i;
        },
        login_neo4j: function() {
            var xhttp = new XMLHttpRequest();
            var _this = this;
            this.login_fail = "";
            xhttp.onreadystatechange = function() {
                if (this.readyState == 4 && this.status == 200) {
                    window.location.href="/GUI.html";
                } else if(this.status == 500) {
                    _this.login_fail = "Try again!";
                }
            };
            xhttp.open("GET", "/login?username=" + this.login.username + "&password=" + this.login.password, true);
            xhttp.send();
            // xhttp.open("POST", "/login", true);
            // xhttp.setRequestHeader("Content-type", "application/json");
            // xhttp.send(JSON.stringify(this.login));
        },
        banned_cut: function(v) {
            if (this.banned_set.includes(v)) {
                var index = this.banned_set.indexOf(v);
                this.banned_set.splice(index, 1);
            } else {
                this.banned_set.push(v);
            }
        },
        switch_to_aaai: function() {
            window.location.href="/aaai.html";
        },
        switch_to_bloodHound: function() {
            window.location.href="/GUI.html";
        },
        get_domain: function() {
            var _this = this;
            var xhttp = new XMLHttpRequest();
            vueinst.loading = true;
            xhttp.onreadystatechange = function() {
                if (this.readyState == 4 && this.status == 200) {
                    vueinst.loading = false;
                    let received = JSON.parse(this.responseText);
                    _this.domain_info = received;
                }
            };
            xhttp.open("GET", "/get_domain", true);
            xhttp.send();
        }
    }
});

vueinst.query = mydata;
function myFunction() {
    document.getElementById("myDropdown").classList.toggle("show");
  }

  // Close the dropdown if the user clicks outside of it
  window.onclick = function(event) {
    if (!event.target.matches('.dropbtn')) {
      var dropdowns = document.getElementsByClassName("dropdown-content");
      var i;
      for (i = 0; i < dropdowns.length; i++) {
        var openDropdown = dropdowns[i];
        if (openDropdown.classList.contains('show')) {
          openDropdown.classList.remove('show');
        }
      }
    }
  }

var s = new sigma(
    {
        renderer: {
            container: document.getElementById("sigma-container"),
            // type: 'canvas'
            type: sigma.renderers.canvas
        },
        settings: {
            drawNodes: true,
            drawLabels: false,
            minEdgeSize: 0.1,
            maxEdgeSize: 2,
            minNodeSize: 1,
            maxNodeSize: 8,
            edgeLabelSize: 'proportional',
            labelSize: 'fixed',
            minArrowSize: 5,
            labelThreshold:30,
            enableHovering: true,
            enableEdgeHovering: true,
            edgeHoverSizeRatio: 2,
            edgeHoverColor: "yellow",
            defaultEdgeHoverColor: '#FF8C00',
            edgeHoverExtremities: true,
            // drawNodes: true,
            // drawLabels: true
        }
    }
);
s.cameras[0].goTo({ x: 0, y: 0, angle: 0, ratio: 0.6 });
var dragListener = sigma.plugins.dragNodes(s, s.renderers[0]);
var graph = { nodes: [], edges: [] };

function generate_graph(graph) {
    s.graph.clear();
    s.graph.read(graph);
    // CustomShapes.init(s);
    // Ask sigma to draw it
    s.refresh();
    // console.log(graph);
    s.cameras[0].goTo({ x: 0, y: 0, angle: 0, ratio: 0.5 });
    s.startForceAtlas2();
    window.setTimeout(function() {s.killForceAtlas2()}, 2000);
}

function get_path() {
    let index = vueinst.query_index;
    console.log(index);
    let query_option = mydata[index];
    let option_index = vueinst.option_index;
    let ready = vueinst.option_ready;
    if (query_option.queryList.length === 1) {
        get_path_now(index);
    } else {
        if (ready) {
            vueinst.option_ready = false;
            console.log("option "+option_index);
            get_path_later(index, option_index);
        } else {
            get_path_info(index);
        }
    }

}
function get_path_now(x) {
    var xhttp = new XMLHttpRequest();
    vueinst.loading = true;
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            vueinst.loading = false;
            graph=JSON.parse(this.responseText);
            if (graph.nodes.length === 0 && graph.edges.length === 0) {
                vueinst.alert = true;
            } else {
                generate_graph(graph);
            }
        }
    };
    xhttp.open("GET", "/get_path_now?indexs="+x, true);
    xhttp.send();
}

function get_path_info(x) {
    var xhttp = new XMLHttpRequest();
    vueinst.loading = true;
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            vueinst.loading = false;
            if (JSON.parse(this.responseText) === []) {
                vueinst.alert = true;
            } else {
                vueinst.query_options = JSON.parse(this.responseText);
                vueinst.query_box = true;
            }

        }
    };
    xhttp.open("GET", "/get_path_info?indexs="+x, true);
    xhttp.send();
}

function get_path_later(x,y) {
    var xhttp = new XMLHttpRequest();
    vueinst.query_options = [];
    vueinst.loading = true;
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            vueinst.loading = false;
            graph=JSON.parse(this.responseText);
            console.log(graph);
            if (graph.nodes.length === 0 && graph.edges.length === 0) {
                vueinst.alert = true;
            } else {
                generate_graph(graph);
            }
        } else if (this.status == 500){
            vueinst.loading = false;
            vueinst.alert = true;
        }
    };
    xhttp.open("GET", "/get_path_now?indexs=" + x + "&option=" + y, true);
    xhttp.send();
}

function ransomulator() {
    var xhttp = new XMLHttpRequest();
    vueinst.loading = true;
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            vueinst.ransom_open = true;
            vueinst.loading = false;
            vueinst.ransom = [];
            vueinst.ransom_title = ["Host name", "Total"];
            var result=JSON.parse(this.responseText);
            //ransom_title
            // if (result[result.length-1].Total >= 0) {
            //     for (var i=0; i<result[result.length-1].Total; i++) {
            //         let title = "Wave "+(i+1);
            //         vueinst.ransom_title.push(title);
            //     }

            // }

            if (vueinst.ransom_comp != "") {
                vueinst.ransom[0] = result.find(comp => comp.Hostname == vueinst.ransom_comp);
                console.log(vueinst.ransom);
                if (vueinst.ransom[0].hasOwnProperty('null')) {
                    delete vueinst.ransom[0].null;
                }
            } else {
                //ransom_items
                vueinst.ransom = result.slice(1, result.length-4);
                //delete null property
                for (var i=0; i<vueinst.ransom.length; i++) {
                    if (vueinst.ransom[i].hasOwnProperty('null')) {
                        delete vueinst.ransom[i].null;
                    }
                }
            }

            if (vueinst.ransom_comp != "") {
                for (var i=0; i<vueinst.ransom[0].length-2; i++) {
                    let title = "Wave "+(i+1);
                    vueinst.ransom_title.push(title);
                }
            } else {
                if (result[result.length-1].Total >= 0) {
                    for (var i=0; i<result[result.length-1].Total; i++) {
                        let title = "Wave "+(i+1);
                        vueinst.ransom_title.push(title);
                    }

                }
            }

            console.log(vueinst.ransom);
            vueinst.ransom_comp = "";
        }
    };
    xhttp.open("GET", "/ransomulator?simulate=" + vueinst.simulate, true);
    xhttp.send();
}

function shothound() {
    var xhttp = new XMLHttpRequest();
    vueinst.shothound = {};
    vueinst.path = {};

    vueinst.loading = true;
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            vueinst.loading = false;
            var data_received = JSON.parse(this.responseText);
            if (data_received.hasOwnProperty('empty')) {
                vueinst.shothound_empty = true;
            } else {
                shothound_empty = false;
                vueinst.shothound = data_received[0];
                vueinst.path = data_received[1];
                if (!vueinst.path.hasOwnProperty('Logical')) {
                    vueinst.path.Logical = 0;
                }
                if (!vueinst.path.hasOwnProperty('Practical')) {
                    vueinst.path.Practical = 0;
                }
                if (!vueinst.path.hasOwnProperty('Percent')) {
                    vueinst.path.Percent = 0;
                }
                vueinst.result_shothound_open = true;
            }


            vueinst.shothound_open = true;
        }
    };
    xhttp.open("GET", "/shothound?source="+vueinst.shothound_input.source+"&target="+vueinst.shothound_input.target, true);
    xhttp.send();
}

function test() {
    console.log(mydata);
}

function raw_query() {
    var xhttp = new XMLHttpRequest();
    vueinst.query_options = [];
    vueinst.loading = true;
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            vueinst.loading = false;
            graph=JSON.parse(this.responseText);
            console.log(graph);
            if (graph.nodes.length === 0 && graph.edges.length === 0) {
                vueinst.alert = true;
            } else {
                generate_graph(graph);
            }
        } else {
            vueinst.loading = false;
        }
    };
    xhttp.open("GET", "/get_path_now?raw_query="+vueinst.raw_query, true);
    xhttp.send();
}

function iterative_cut() {
    var xhttp = new XMLHttpRequest();
    vueinst.loading = true;
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            vueinst.loading = false;
            vueinst.iterative_open = true;
            vueinst.banned_set = [];
            var result=JSON.parse(this.responseText);
            if (result.hasOwnProperty('impossible')) {
                vueinst.cut_empty = true;
            } else {
                vueinst.cut_empty = false;
                vueinst.cuts = result;
                console.log(result);
                // console.log()
                // console.log(database.nodes.find(node => node.properties.objectid == 'S-1-5-21-883232822-274137685-4173207997-515').properties.name);
                // console.log(database.nodes);
                // vueinst.cuts = Object.keys(result).forEach(function(key) {
                //     result[key][0] = database.nodes.find(node => node.properties.objectid == result[key][0]).properties.name;
                //     result[key][1] = database.nodes.find(node => node.properties.objectid == result[key][1]).properties.name;
                // });
                // for (let i=0; i<vueinst.cuts.length; i++) {
                //     vueinst.cuts[i][0] = database.nodes.find(node => node.properties.objectid == vueinst.cuts[i][0]).properties.name;
                //     vueinst.cuts[i][1] = database.nodes.find(node => node.properties.objectid == vueinst.cuts[i][1]).properties.name;

                // }
                // console.log(vueinst.cuts);
                // vueinst.cuts = result;
            }

        }
    };
    xhttp.open("GET", "/iterative_cut?bannedSet="+vueinst.banned_set, true);
    xhttp.send();
}

// var path_set = { nodes: [], edges: {} };
var edges_found =[];
function computeAndDrawPath_regret(pathColor) {
    for (let i=0; i<edges_found.length; i++) {
        var edge = s.graph.edges(edges_found[i].id);
        edge.color = pathColor;
    }
}

function regret_graph() {
    computeAndDrawPath_regret("black");

    edges_found.forEach(edge => s.graph.edges(edge.id).color = "black");

    edges_found = vueinst.path_set.edges[vueinst.regret_option];
    edges_found.forEach(edge => s.graph.edges(edge.id).color = "red");
    vueinst.loading = false;
    s.refresh();
}
function regret_matching() {
    let x = vueinst.cfr.source;
    let y = vueinst.cfr.target;
    var xhttp = new XMLHttpRequest();
    vueinst.loading = true;
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            vueinst.loading = false;
            let received = JSON.parse(this.responseText);
            vueinst.path_set.nodes = received.nodes;
            vueinst.path_set.edges = received.edges;
            console.log(vueinst.path_set);
            // console.log(graph);
            if (received.nodes.length === 0 && received.edges.length === 0) {
                vueinst.alert = true;
            } else {
                vueinst.regret_open = true;
                //initiate a graph to render
                let path_graph = {};
                path_graph["nodes"] = vueinst.path_set.nodes;
                path_graph["edges"] = [];

                //getting the graph info of edges
                var db_graph_edges = vueinst.path_set.edges;

                for (let key in db_graph_edges) {
                    for (let item of db_graph_edges[key]) {
                        if (!path_graph["edges"].some(obj => obj.id.toString() === item.id.toString())) { //if the edges does not exist, append it
                            path_graph["edges"].push(item);
                        }
                    }
                }
                console.log(path_graph);

                generate_graph(path_graph);
                edges_found = vueinst.path_set.edges[vueinst.regret_option];
                edges_found.forEach(edge => s.graph.edges(edge.id).color = "red");
                s.refresh();

            }
        }
    };
    xhttp.open("GET", "/regret_matching?source=" + x + "&target=" + y, true);
    xhttp.send();
}

function regret_matching_v2() {
    let x = vueinst.cfr.source;
    let y = vueinst.cfr.target;
    var xhttp = new XMLHttpRequest();
    vueinst.loading = true;
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            vueinst.loading = false;
            let received = JSON.parse(this.responseText);
            vueinst.path_set.nodes = received.nodes;
            vueinst.path_set.edges = received.edges;
            console.log(vueinst.path_set);
            // console.log(graph);
            if (received.nodes.length === 0 && received.edges.length === 0) {
                vueinst.alert = true;
            } else {
                vueinst.regret_open = true;
                //initiate a graph to render
                let path_graph = {};
                path_graph["nodes"] = vueinst.path_set.nodes;
                path_graph["edges"] = [];

                //getting the graph info of edges
                var db_graph_edges = vueinst.path_set.edges;

                for (let key in db_graph_edges) {
                    for (let item of db_graph_edges[key]) {
                        if (!path_graph["edges"].some(obj => obj.id === item.id)) { //if the edges does not exist, append it
                            path_graph["edges"].push(item);
                        }
                    }
                }
                console.log(path_graph);

                generate_graph(path_graph);
                edges_found = vueinst.path_set.edges[vueinst.regret_option];
                edges_found.forEach(edge => s.graph.edges(edge.id).color = "red");
                s.refresh();

            }
        }
    };
    xhttp.open("GET", "/regret_matching_v2?source=" + x + "&target=" + y, true);
    xhttp.send();
}

var c = s.camera;
function zoomin() {
    sigma.misc.animation.camera(c, {
        ratio: c.ratio / c.settings('zoomingRatio')
      }, {
        duration: 200
      });

}

function zoomout() {
    sigma.misc.animation.camera(c, {
        ratio: c.ratio * c.settings('zoomingRatio')
      }, {
        duration: 200
      });
}

s.bind('clickNode rightClickNode', function(e) {
    vueinst.searcher = 'nodeInfo'
    vueinst.node_info = true;
    vueinst.props = e.data.node.properties;
    if (vueinst.props.hasOwnProperty('lastlogon')) {
        delete vueinst.props.lastlogon;
    }
    if (vueinst.props.hasOwnProperty('pwdlastset')) {
        delete vueinst.props.pwdlastset
    }
    console.log(e.data.node);
});


function computeAndDrawPath(srcId, destId, pathColor) {
    var path = s.graph.astar(srcId, destId, {
      undirected: true
    });console.log(path);

    if(path) {
      for(var i = 0; i < path.length; i++) {
        if (i < path.length) {
            var edge_found = graph.edges.find( edge_found => edge_found.source === path[i].id && edge_found.target === path[i+1].id);
            if (edge_found) {
                edges_found.push(edge_found);
                var edge = s.graph.edges(edge_found.id);
                if(edge) {
                    edge.color = pathColor;
                }
            }
        }
      }
    }

    // var srcNode = s.graph.nodes(srcId),
    //     destNode = s.graph.nodes(destId);

    // srcNode.color = boundaryColor;
    // destNode.color = boundaryColor;

    s.refresh();
}
s.bind('overNode', function(e) {
    edges_found = [];
    console.log()
    computeAndDrawPath(e.data.node.id, vueinst.domain_info.id_domain, "red");
});

s.bind('outNode', function (e) {
    for (var i=0; i<edges_found.length; i++) {
        var edge = s.graph.edges(edges_found[i].id);
        edge.color = "#000";
    }
    s.refresh();
});

function aaai() {
    vueinst.loading = true;
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            vueinst.loading = false;
            let received = JSON.parse(this.responseText);
            vueinst.aaai_result = received.items;
            vueinst.aaai_open = true;

        } else if (this.status == 500){
            vueinst.loading = false;
        }
    };
    xhttp.open("GET", "/aaai?budget=" + vueinst.aaai_input.budget+ "&start=" + vueinst.aaai_input.start, true);
    xhttp.send();
}





// var graph = {
//     nodes: [
//       { id: "n0", label: "A node", x: 0, y: 0, size: 7, color: '#008cc2' },
//       { id: "n1", label: "Another node", x: 3, y: 1, size: 7, color: '#008cc2' },
//       { id: "n2", label: "And a last one", x: 1, y: 3, size: 7, color: '#E57821' },
//       { id: "n3", label: "Node 3", x: 2, y: 4, size: 7, color: '#E57821' },
//       { id: "n4", label: "Node 4 ", x: 3, y: 6, size: 7, color: '#E57821' },
//       { id: "n5", label: "Node 5", x: 9, y: 8, size: 7, color: '#E57821' }
//     ],
//     edges: [
//       { id: "e0", label: "Edge 1", source: "n0", target: "n1", color: '#282c34', type:'arrow', size:2 },
//       { id: "e1", label: "Edge 2", source: "n1", target: "n2", color: '#282c34', type:'arrow', size:2},
//       { id: "e2", label: "Edge 3", source: "n2", target: "n0", color: '#FF0000', type:'arrow', size:2},
//       { id: "e3", label: "Edge 4", source: "n2", target: "n3", color: '#FF0000', type:'arrow', size:2},
//       { id: "e4", label: "Edge 5", source: "n3", target: "n4", color: '#FF0000', type:'arrow', size:2},
//       { id: "e5", label: "Edge 6", source: "n4", target: "n5", color: '#FF0000', type:'arrow', size:2}
//     ]
//   }

//   sigma.classes.graph.addMethod('hoverIncommingEdges', function(e) {
//     var id = e.data.node.id;
//     var inNeighbors = this.inNeighborsIndex[id];
//     for (var i in inNeighbors) {
//       for (var j in inNeighbors[i]) {
//         inNeighbors[i][j].size = 2;  // Hover the edge like this
//         inNeighbors[i][j].color = '#000'
//       }
//     }
//   });

//   s.bind('overNode', function (e) {
//     s.graph.hoverIncommingEdges(e);
//     s.refresh();
//   });

  // Load the graph in sigma
//   s.graph.read(graph);
//   // Ask sigma to draw it
//   s.refresh();

//   s.startForceAtlas2();
// window.setTimeout(function() {s.killForceAtlas2()}, 10000);


//-----------REFERENCE------------------
//HTTP request
// function ransomulator() {
//     var xhttp = new XMLHttpRequest();
//     xhttp.onreadystatechange = function() {
//         // if (this.readyState == 4 && this.status == 200) {
//         //     var result=JSON.parse(this.responseText);
//         //     _this.wave = result.low;
//         // }
//     };
//     xhttp.open("GET", "", true);
//     xhttp.send();
// }
