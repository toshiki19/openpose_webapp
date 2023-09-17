document.addEventListener("DOMContentLoaded", function () {
    // JSONファイルのパス
    var jsonPath = "{{ json_path }}";  // Flaskから提供されるJSONファイルのパス

    // 解析結果を表示するための要素
    var keypointsContainer = document.getElementById("keypoints-container");
    var keypointsCanvas = document.getElementById("keypoints-canvas");
    var ctx = keypointsCanvas.getContext("2d");

    // JSONデータを取得し、キーポイントを描画
    fetch(jsonPath)
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            // キーポイントを描画する関数を呼び出す
            drawKeypoints(data);
        })
        .catch(function (error) {
            console.error("Error fetching JSON data: " + error);
        });

    // キーポイントを描画する関数
    function drawKeypoints(data) {
        // キーポイントの描画ロジックをここに追加
        // dataを使用してキーポイントをキャンバス上に描画
    }
});
