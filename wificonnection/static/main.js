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

            console.log("real?")

            var wifiListDiv = `<div class="wifi-connect">
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





            var div = $('<div/>')
            var wifiDiv = $('<div class="wifi-connect" />')

            var wifiTitleDiv = $('<div class="wifi-title" />')
            var wifiTitSpan = $('<span class="tit-wifi" />').text("wifi")
            var wifiTxtStatus = $('<span class="txt-status active" />').text("wifi is connectig")

            var toggleBtn = $('<a href="javascript:;" class="toggle-wrap active" />')
            var toggleBar = $('<span class="toggle-bar" />')
            var toggleThumb = $('<span class="toggle-thumb" />')

            var progressImg = $('<img class="progress"/>').attr('src','./progress.svg')

            var retryBtn = $('<a href="javascript:;" class="btn-retry" />')
            var retryImg = $('<img class="retry" />').attr('src','./retry.svg')

            progressImg.attr({
                rel: 'stylesheet',
                type: 'text/css',
                src: requirejs.toUrl('./progress.svg')
            })

            retryImg.attr({
                rel: 'stylesheet',
                type: 'text/css',
                src: requirejs.toUrl('./retry.svg')
            })

            wifiTitleDiv.append(wifiTitSpan).append(wifiTxtStatus)
            toggleBtn.append(toggleBar).append(toggleThumb)
            retryBtn.append(retryImg)

            wifiDiv.append(wifiTitleDiv).append(toggleBtn).append(progressImg).append(retryBtn)

            div.append(wifiListDiv)
            $('.progress').attr('src','./progress.svg')
            $('.retry').attr('src','./retry.svg')
            var wifiListUl = $('<ul class="wifi-list"/>')

            // toggleDiv.append(toggleBar).append(toggleThumb)

            testData = {
                "statusText" : "interface off",
                "current_wifi_data" : [{
                    "ssid" : "test",
                    "psk" : "PSK",
                    "signal" : -47,
                    "status" : true
                }],
                "whole_wifi_data" : [{
                    ssid: "test1",
                    psk : "PSK",
                    signal : -47
                },{
                    ssid: "test2",
                    psk : "PSK",
                    signal : -56
                }]
            }

            function addList(name) {
                var wifiListLi = $('<li class="wifi-item" />')
                var wifiButtonA = $('<a href="javascript:;" class="btn-wifi" />')
                var wifiNameSpan = $('<span class="wifi-name" />')
                var wifiPrivateSpan = $('<span class="wifi-private" />')
                wifiListUl.append(wifiListLi.append(wifiButtonA.append(wifiNameSpan.text(name)).append(wifiPrivateSpan)))
                $('.progress').css("display", "none")
                div.append(wifiListUl)
            }

            $(document).on('click', '.toggle-wrap', function(){
                if($(this).hasClass('active')){
                    $('.progress').css("display", "none")
                    $('.btn-retry').css("display", "none")
                    $(this).removeClass('active')
                }else {
                    $('.progress').css("display", "block")
                    $('.btn-retry').css("display", "block")
                    $(this).addClass('active')
                }
            })

            
            var settings = {
                url : '/wifi/scan',
                processData : false,
                type : "GET",
                dataType: "json",
                contentType: 'application/json',
                success: function(data) {
                    if(data.statusText === "interface off"){
                        $('.progress').css("display", "none")
                        $('.btn-retry').css("display", "none")
                    } else {
                        $('.toggle-wrap').addClass('active')
                        $('.progress').css("display", "block")
                        $('.btn-retry').css("display", "block")
                        data.current_wifi_data.forEach(function(v){
                            addList(v.SSID)
                        })
                        data.whole_wifi_data.forEach(function(v){
                            addList(v.SSID)
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

            var payload = {
                'SSID' : "DREAMPLUS_13F",
                'PSK' : "dreamtt3!"
              };
            var settingSettings = {
                url : '/wifi/setting',
                processData : false,
                type : "PUT",
                dataType: "json",
                data: JSON.stringify(payload),
                contentType: 'application/json',
                success: function(data) {

                    //console.log(data)
                    console.log('fun')
                },
                error: function(data) {
                    console.log('error')
                }

            };
            $.ajax(settingSettings);
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