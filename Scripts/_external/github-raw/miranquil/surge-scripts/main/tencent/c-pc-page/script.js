const regex = /pfurl=([^&]*)/;
const match = $request.url.match(regex);

if (match && match[1]) {
  const encodedURL = match[1];
  origin_url = decodeURIComponent(encodedURL);
  $done({
    response: {
      status: 302,
      headers: { Location: decodeURIComponent(encodedURL) },
    },
  });
} else {
  $done();
}
