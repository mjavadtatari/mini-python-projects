// Site definitions – add as many as you need
const SITES = [
  {
    id: "melodify",
    name: "Melodify",
    urlPattern: /desktop\.melodify\.app/,
    selectors: {
      title:
        "/html/body/div/div/div[2]/div[2]/div[2]/div[1]/div[2]/span/div/span",
      thumbnail:
        "/html/body/div/div/div[2]/div[2]/div[2]/div[1]/div[1]/div/span/img",
    },
    streamUrlPattern:
      /\/serve\/v1\/track\/[a-f0-9]+\/[a-f0-9]+\/track_demo\.mp3$/,
    transformDemoTo320: (demoUrl) =>
      demoUrl.replace("track_demo.mp3", "track_320.mp3"),
  },
  // Future site example:
  // {
  //   id: "example",
  //   name: "Example Music Site",
  //   urlPattern: /example\.com\/music/,
  //   selectors: {
  //     title: '//div[@class="song-title"]',
  //     thumbnail: '//img[@class="cover"]/@src'
  //   },
  //   streamUrlPattern: /\/stream\/[^\/]+\.mp3/,
  //   transformDemoTo320: (demoUrl) => demoUrl.replace(".mp3", "_320.mp3")
  // }
];
