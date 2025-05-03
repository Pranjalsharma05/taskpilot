$(document).ready(function () {
  $(".load-content").on("click", function (e) {
      e.preventDefault();
      var url = $(this).attr("href");
      var target = $(this).data("target");

      $.ajax({
          url: url,
          type: "GET",
          success: function (data) {
              $(target).html(data);
          },
          error: function () {
              alert("Failed to load content.");
          }
      });
  });
});
