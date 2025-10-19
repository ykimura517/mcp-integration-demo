import Chat from '@/components/Chat';

export default function Home() {
  return (
    <main className='flex min-h-screen flex-col items-center justify-center bg-gray-100 dark:bg-gray-900'>
      <div className='w-full max-w-4xl h-[80vh] bg-white dark:bg-gray-800 rounded-lg shadow-lg'>
        <Chat />
      </div>
    </main>
  );
}
