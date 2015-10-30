$(function () {
    'use strict';
    // Change this to the location of your server-side upload handler:
    var url = '/',
        uploadButton = $('<button/>')
            .addClass('btn btn-primary')
            .prop('disabled', true)
            .text('Processing...')
            .on('click', function () {
                var $this = $(this),
                    data = $this.data();
                $this
                    .off('click')
                    .text('Abort')
                    .on('click', function () {
                        $this.remove();
                        data.abort();
                    });
                data.submit().always(function () {
                    $this.remove();
                });
            });
    $('#fileupload').fileupload({
        url: url,
        dataType: 'json',
        autoUpload: false,
        maxFileSize: 1000,
        // Enable image resizing, except for Android and Opera,
        // which actually support image resizing, but fail to
        // send Blob objects via XHR requests:
        disableImageResize: /Android(?!.*Chrome)|Opera/
            .test(window.navigator.userAgent),
        previewMaxWidth: 100,
        previewMaxHeight: 100,
        previewCrop: true
    }).on('fileuploadadd', function (e, data) {
        data.context = $('<div/>').appendTo('#files');
        $.each(data.files, function (index, file) {
            var node = $('<p/>')
                    .append($('<span/>').text(file.name));
            if (!index) {
                node
                    .append('<br>')
                    .append(uploadButton.clone(true).data(data));
            }
            node.appendTo(data.context);
        });
    }).on('fileuploadprocessalways', function (e, data) {
        var index = data.index,
            file = data.files[index],
            node = $(data.context.children()[index]);
        if (file.preview) {
            node
                .prepend('<br>')
                .prepend(file.job_id);
        }
        if (file.error) {
            node
                .append('<br>')
                .append($('<span class="text-danger"/>').text(file.error));
        }
        if (index + 1 === data.files.length) {
            data.context.find('button')
                .text('Upload')
                .prop('disabled', !!data.files.error);
        }
    }).on('fileuploadprogressall', function (e, data) {
        var progress = parseInt(data.loaded / data.total * 100, 10);
        $('#progress .progress-bar').css(
            'width',
            progress + '%'
        );
    }).on('fileuploaddone', function (e, data) {
        $.each(data.result.files, function (index, file) {
            if (file.url) {
                var link = $('<a>')
                    .attr('target', '_blank')
                    .prop('href', file.url);
                $(data.context.children()[index])
                    .wrap(link);
            } else if (file.error) {
                var error = $('<span class="text-danger"/>').text(file.error);
                $(data.context.children()[index])
                    .append('<br>')
                    .append(error);
            } else if (file.job_id) {
                var link = $('<span class="text-success"/>').html('Job ID: ' + file.job_id);
                $(data.context.children()[index])
                    .append('<br>')
                    .append(link);
                var opts = {top:'35%', left:'80%', scale:0.5, position:'relative'};
                var spinner = new Spinner(opts).spin();
                $(data.context.children()[index])
                    .append('<br>')
                    .append('<div>').append(spinner.el).append('</div>');
                function ajax_request(job_id) {
                  $.ajax({
                    url: '/status/'+job_id,
                    dataType: 'json',
                    error: function(xhr_data) {
                      // terminate the script
                        alert('error');
                    },
                    success: function(xhr_data) {
                      if (xhr_data.status == 'pending') {
                        console.log('pending');
                        setTimeout(function() { ajax_request(xhr_data.job_id); }, 5000);
                      } else {
                        var link = $('<span class="text-success"/>').html('<a href=results/'+xhr_data.job_id+'>Results</a>');
                        $(data.context.children()[index]).html(link);
                      }
                    },
                    contentType: 'application/json'
                  });
                };
                var response = ajax_request(file.async_id);
            }
        });
    }).on('fileuploadfail', function (e, data) {
        $.each(data.files, function (index) {
            var error = $('<span class="text-danger"/>').text('File upload failed.');
            $(data.context.children()[index])
                .append('<br>')
                .append(error);
        });
    }).prop('disabled', !$.support.fileInput)
        .parent().addClass($.support.fileInput ? undefined : 'disabled');
});
