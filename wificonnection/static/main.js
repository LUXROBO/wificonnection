define(['require','base/js/namespace','base/js/dialog','jquery'],function(requirejs, IPython, dialog, $){

    // we will define an action here that should happen when we ask to clear and restart the kernel.
    var search_wifi  = {
        help: 'wifi',
        icon : 'fa-wifi',
        help_index : '',
        handler : function (env) {
            $('<link />').attr({
                rel: 'stylesheet',
                type: 'text/css',
                href: requirejs.toUrl('./main.css')
            }).appendTo('head')
            var div = $('<div/>')
            var wifiConnectDiv = `<div class="wifi-connect">
                                 <div class="wifi-title">
                                    <span class="tit-wifi">Wifi</span>
                                    <span class="txt-status active">wifi is connecting</span>
                                 </div>
                                 <a href="javascript:;" class="toggle-wrap active">
                                    <span class="toggle-bar"></span>
                                    <span class="toggle-thumb"></span>
                                 </a>
                                 <img class="progress" rel="stylesheet" type="text/css">
                                 <a href="javascript:;" class="btn-retry">
                                    <img class="retry" src="/nbextensions/wificonnection/retry.svg" rel="styleshhet" type="text/css">
                                 </a> 
                               </div>`


            var settings = {
            url : '/wifi/scan',
            processData : false,
            type : "GET",
            dataType: "json",
            contentType: 'application/json',
            success: function(data) {
                if(data.statusText === "interface off"){
                    console.log("off")
                    $('.progress').css("display", "none")
                    $('.btn-retry').css("display", "none")
                } else {
                    console.log("on")
                    $('.toggle-wrap').addClass('active')
                    $('.progress').css("display", "block")
                    $('.btn-retry').css("display", "block")
                    data.current_wifi_data.forEach(function(v){
                        addList(v.SSID,v.PSK,v.SIGNAL,v.STATUS)
                    })
                    data.whole_wifi_data.forEach(function(v){
                        addList(v.SSID,v.PSK,v.SIGNAL,v.STATUS)
                    })

                }
                console.log(data)
            },
            error: function(data) {
                // if(testData.statusText !== "interface off"){
                //     $('.progress').css("display", "none")
                //     $('.btn-retry').css("display", "none")
                // } else {
                //     testData.current_wifi_data.forEach(function(v){
                //         addList(v.ssid)
                //     })
                //     testData.whole_wifi_data.forEach(function(v){
                //         addList(v.ssid)
                //     })
                //     $('.toggle-wrap').addClass('active')
                //     $('.progress').css("display", "block")
                // }
            }

            };
            div.append(wifiConnectDiv)
            $('.progress').attr('src','./progress.svg')
            $('.retry').attr('src','./retry.svg')

            function addList(name, psk, signal, status=false) {
                var wifiListUl = $('<ul class="wifi-list"/>')
                var signalLevel = 0;
                if(signal > -20) {
                    signalLevel = 4
                } else if( -20 > signal >= -30) {
                    signalLevel = 3
                } else if( -30 > signal >= -40) {
                    signalLevel = 2
                } else if( -40 > signal >= -50) {
                    signalLevel = 1
                } else if( -50 > signal) {
                    signalLevel = 0
                }

                function current (state) {
                    return state === true ?`<img class="wifi-current" src="/nbextensions/wificonnection/selected.svg" rel="stylesheet" type="text/css" />` : ""
                }

                function private (private) {
                    return private === "PSK" ? `<img class="wifi-private" src="/nbextensions/wificonnection/lock.svg" rel="stylesheet" type="text/css"></img>` : ""
                }

                var wifiListItem = `<li class="wifi-item">
                                      <a href="javascript:;" class="btn-wifi">
                                        <span class="wifi-name">${name}</span>` + current(status)
                                         + private(psk) +
                                        `<img class="wifi-strength" src="/nbextensions/wificonnection/wifi-${signalLevel}.svg" rel="stylesheet" type="text/css">
                                      </a>
                                    </li>`
                wifiListUl.append(wifiListItem)
                $('.progress').css("display", "none")
                div.append(wifiListUl)
            }

            function resetList() {
                $('.wifi-list').remove()
            }

            $(document).on('click', '.toggle-wrap', function(){
                if($(this).hasClass('active')){
                    $('.progress').css("display", "none")
                    $('.btn-retry').css("display", "none")
                    $(this).removeClass('active')
                    resetList()
                }else {
                    $('.progress').css("display", "block")
                    $('.btn-retry').css("display", "block")
                    $(this).addClass('active')
                    $.ajax(settings);
                }
            })

            $(document).on('click', '.btn-wifi', function(){
                var targetName = $(this).find(".wifi-name").text()
                var wifiPrivate = !!($(this).find(".wifi-private").length)

                var modalTitle = `<div class="tit-wrap">
                                    <a href="javascript:;" class="btn-back">
                                    <img class="back" src="/nbextensions/wificonnection/icon-back.svg" rel="stylesheet" type="text/css" style="display: block;" />
                                    </a>
                                    <div class="tit-input">Input password</div>
                                  </div>`

                var passwordDiv = `<div class="password-box">
                                     <p class="tit-password">WiFi "${targetName}" is required password.</p>
                                     <div class="password-wrap invalid">
                                        <input class="inp-password" type="password" placeholder="Input password">
                                        <a href="javascript:;" class="btn-visibility">
                                          <img class="password-visibility active" src="/nbextensions/wificonnection/innvisibility.svg" rel="stylesheet" type="text/css"/>
                                        </a>
                                        <span class="txt-invalid"> Invalid password. please try again</span>
                                      </div>
                                      <label class="chk-remeber">Remeber this network
                                        <input type="checkbox" checked="checked"/>
                                        <span class="checkmark"></span>
                                      </label>
                                   </div>`
                var modalHeaderDiv = $('<div/>')
                var modalBodyDiv = $('<div/>')

                modalHeaderDiv.append(modalTitle)
                modalBodyDiv.append(passwordDiv)

                console.log(wifiPrivate)
                console.log(targetName)

                dialog.modal({
                    body: modalBodyDiv ,
                    title: 'Input password',
                    dialogClass: 'test',
                    // buttons: {'Commit and Push':
                    //             { class:'btn-primary btn-large',
                    //               click:on_ok
                    //             },
                    //           'Cancel':{}
                    //     },
                    notebook:env.notebook,
                    keyboard_manager: env.notebook.keyboard_manager,
                })
            })






            
            var settings = {
                url : '/wifi/scan',
                processData : false,
                type : "GET",
                dataType: "json",
                contentType: 'application/json',
                success: function(data) {
                    if(data.statusText === "interface off"){
                        console.log("off")
                        $('.progress').css("display", "none")
                        $('.btn-retry').css("display", "none")
                    } else {
                        console.log("on")
                        $('.toggle-wrap').addClass('active')
                        $('.progress').css("display", "block")
                        $('.btn-retry').css("display", "block")
                        data.current_wifi_data.forEach(function(v){
                            addList(v.SSID,v.PSK,v.SIGNAL,v.STATUS)
                        })
                        data.whole_wifi_data.forEach(function(v){
                            addList(v.SSID,v.PSK,v.SIGNAL,v.STATUS)
                        })

                    }
                    console.log(data)
                },
                error: function(data) {
                    // if(testData.statusText !== "interface off"){
                    //     $('.progress').css("display", "none")
                    //     $('.btn-retry').css("display", "none")
                    // } else {
                    //     testData.current_wifi_data.forEach(function(v){
                    //         addList(v.ssid)
                    //     })
                    //     testData.whole_wifi_data.forEach(function(v){
                    //         addList(v.ssid)
                    //     })
                    //     $('.toggle-wrap').addClass('active')
                    //     $('.progress').css("display", "block")
                    // }
                }

            };
            $.ajax(settings);

            dialog.modal({
                body: div ,
                title: 'Wifi list',
                // buttons: {'Commit and Push':
                //             { class:'btn-primary btn-large',
                //               click:on_ok
                //             },
                //           'Cancel':{}
                //     },
                notebook:env.notebook,
                keyboard_manager: env.notebook.keyboard_manager,
            })

            // var payload = {
            //     'SSID' : "test",
            //     'PSK' : "test111"
            //   };
            // var settingSettings = {
            //     url : '/wifi/setting',
            //     processData : false,
            //     type : "PUT",
            //     dataType: "json",
            //     data: JSON.stringify(payload),
            //     contentType: 'application/json',
            //     success: function(data) {
                   
            //         console.log(data)
            //     },
            //     error: function(data) {

            //     }

            // };
            // $.ajax(settingSettings);
        }
    }

    function _on_load(){

        // log to console
        console.info('wifis')

        // register new action
        var action_name = IPython.keyboard_manager.actions.register(search_wifi, 'search wifi list')

        // add button for new action
        IPython.toolbar.add_buttons_group([action_name])

    }

    return {load_ipython_extension: _on_load };
})

