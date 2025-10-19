import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const { messages } = await req.json();
  //   frontendのみホストマシンで直接動作させる想定なのでlocalhostを指定
  //   const webAppUrl = process.env.WEB_APP_URL || 'http://web_app:8000/api/chat';
  const webAppUrl = process.env.WEB_APP_URL || 'http://localhost:8000/api/chat';

  try {
    const response = await fetch(webAppUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ messages }),
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error(`Error from web_app: ${response.status} ${errorData}`);
      return NextResponse.json(
        { error: 'Backend service error', details: errorData },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Error fetching from web_app:', error);
    return NextResponse.json(
      { error: 'Internal Server Error', details: error.message },
      { status: 500 }
    );
  }
}
